import json
import os
from urllib.parse import urlparse

from django.conf import settings as django_settings
from django.db.models import Count, Q
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse, HttpResponseBadRequest

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.core.exceptions import ObjectDoesNotExist, EmptyResultSet

from .models import tbl_Authentication, Subtree
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors

from DataVisualization.forms import FileForm, UpdateFileForm
from DataVisualization.models import Document, Commentary
from DataVisualization.utilities.ExcelParser import ExcelParser

from cryptography.fernet import Fernet

import requests

TARGETS = ["target_group", "target_person", "target_stereotype"]
FEATURES = ["argumentation", "constructiveness", "sarcasm", "mockery", "intolerance",
            "improper_language", "insult",
            "aggressiveness"]
FILTERS = ["highlight_toxicity_0", "highlight_toxicity_1", "highlight_toxicity_2", "highlight_toxicity_3"] + \
          ["highlight_stance_neutral", "highlight_stance_positive", "highlight_stance_negative"] + \
          ["highlight_" + target for target in TARGETS] + \
          ["highlight_features_" + feature for feature in FEATURES] + \
          ["highlight_OR_selectAll_toxicity", "highlight_OR_selectAll_stance", "highlight_OR_selectAll_target",
           "highlight_OR_selectAll_features"] + \
          ["highlight_AND_selectAll_target", "highlight_AND_selectAll_features"]

COMMONS = ["and_group", "or_group"]

LAYOUTS = ["Tree", "Force", "Radial"]
TREE_LAYOUT = "tree_layout_button"
FORCE_LAYOUT = "force_layout_button"
RADIAL_LAYOUT = "radial_layout_button"
CIRCLE_LAYOUT = "circle_layout_button"

MAIN_OUTPUT = 'output.json'
POPUP_OUTPUT = 'output_popup.json'


def index(request):
    storage_clear = request.GET.get('storageClear', '')
    error_message = request.GET.get('chatbotError', '')
    if (error_message):
        error_message = get_chat_error_message(error_message)

    return render(request, 'index.html', context={'documents_uploaded': get_all_documents(), 'user': request.user,
                                                  'storage_clear': storage_clear, 'chatbot_error': error_message})


def storage_clear_index(request, clear_type):
    return redirect(reverse('index') + '?storageClear=' + clear_type)


def get_all_documents():
    return Document.objects.all()


@require_POST
def save_first_login(request):
    user = getattr(request, 'user', None)
    user.chatprofile.first_login = request.POST['first_login']
    user.save()
    return HttpResponse(status=204)


def generate_dataset(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', True):
        return HttpResponseBadRequest("open_document_no_active_session")

    # CURRENT ITEM
    # ---------------------------------------------------------------------------------
    selected_item = None
    if "from_button" in request.POST.keys():
        selected_item = request.POST['from_button']
    if "selected_data" in request.POST.keys():
        selected_item = request.POST["selected_data"]

    # ---------------------------------------------------------------------------------
    # JSON PARSING & CURRENT DATASET
    # ---------------------------------------------------------------------------------
    auxiliar_generate_dataset(request, selected_item)
    # ---------------------------------------------------------------------------------
    return HttpResponse("/static/" + MAIN_OUTPUT)


def auxiliar_generate_dataset(request, selected_item):
    action_popup = request.POST.get(
        'action_popup')  # Action to be performed in the Popup or Main window (swap, send_to_popup, send_to_main)

    is_popup_subtree = False  # The popup is closed, or there is a complete graph in the popup
    is_main_subtree = False  # There is a complete graph in the main window

    if request.POST.get('main_subtree_id'):
        is_main_subtree = True  # There is a subtree in the Main window
        main_subtree = Subtree.objects.get(pk=request.POST["main_subtree_id"])
        main_nodes = main_subtree.node_ids
        main_selected_item_popup = main_subtree.document.description
    elif request.POST.get('main_subtree_nodes_ids'):
        is_main_subtree = True  # There is a subtree in the Main window
        main_nodes = list(map(int, request.POST['main_subtree_nodes_ids'].split(",")))
        main_selected_item_popup = request.POST['main_subtree_document_description']

    if request.POST.get('popup_subtree_id'):
        is_popup_subtree = True  # There is a subtree in the Popup
        popup_subtree = Subtree.objects.get(pk=request.POST["popup_subtree_id"])
        popup_nodes = popup_subtree.node_ids
        popup_selected_item_popup = popup_subtree.document.description
    elif request.POST.get('popup_subtree_nodes_ids'):
        is_popup_subtree = True  # There is a subtree in the Popup
        popup_nodes = list(map(int, request.POST['popup_subtree_nodes_ids'].split(",")))
        popup_selected_item_popup = request.POST['popup_subtree_document_description']

    popup_graph_info = request.POST.get('popup_graph_info', None)

    if action_popup == "swap" or action_popup == "send_to_main" or (
            action_popup == "send_to_popup" and popup_graph_info):
        # There is a subtree in the Popup
        if is_popup_subtree:
            try:
                dataset_first_level, doc = get_current_dataset_popup(request, popup_nodes, popup_selected_item_popup)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            # The use of the 'save_data_to_JSON_popup' function indicates that a subtree is being generated.
            # The 'MAIN_OUTPUT' parameter indicates that the subtree is sent to the main window.
            save_data_to_JSON_popup(dataset_first_level, popup_nodes, doc,
                                    MAIN_OUTPUT)  # The subtree is sent to the Main window

        # There is no subtree in the Popup
        else:
            try:
                dataset, doc = get_current_dataset(request, selected_item)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            # Filter first level childs
            first_level = dataset.filter(comment_level=1)
            save_data_to_JSON(first_level, doc)  # The complete graph is sent to the Main window

    if action_popup == "send_to_popup" and not popup_graph_info:
        try:
            dataset, doc = get_current_dataset(request, selected_item)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("document_not_exist")
        # Filter first level childs
        first_level = dataset.filter(comment_level=1)
        save_data_to_JSON(first_level, doc)  # The complete graph is sent to the Main window

    if action_popup == "swap" or action_popup == "send_to_popup":
        # There is a subtree in the Main window
        if is_main_subtree:
            try:
                dataset_first_level, doc = get_current_dataset_popup(request, main_nodes, main_selected_item_popup)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            # The use of the 'save_data_to_JSON_popup' function indicates that a subtree is being generated.
            # By default, if the last parameter is not passed, the subtree is sent to the Popup.
            save_data_to_JSON_popup(dataset_first_level, main_nodes, doc)  # The subtree is sent to the Popup

        # There is no subtree in the Main window
        else:
            try:
                dataset, doc = get_current_dataset(request, selected_item)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            first_level = dataset.filter(comment_level=1)
            # The use of the 'save_data_to_JSON' function indicates that a complete graph is being generated.
            # The 'POPUP_OUTPUT' parameter indicates that the complete graph is sent to the Popup.
            save_data_to_JSON(first_level, doc, POPUP_OUTPUT)

    elif not action_popup:
        # The popup is open and displays a graph
        if (popup_graph_info):
            # There is a subtree in the Popup
            if is_popup_subtree:
                try:
                    dataset_first_level, doc = get_current_dataset_popup(request, popup_nodes,
                                                                         popup_selected_item_popup)
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest("document_not_exist")
                # The use of the 'save_data_to_JSON_popup' function indicates that a subtree is being generated.
                # The 'MAIN_OUTPUT' parameter indicates that the subtree is sent to the main window.
                save_data_to_JSON_popup(dataset_first_level, popup_nodes, doc)  # The subtree is sent to the Main window

            # There is no subtree in the Popup
            else:
                try:
                    dataset, doc = get_current_dataset(request, selected_item)
                except ObjectDoesNotExist:
                    return HttpResponseBadRequest("document_not_exist")
                # Filter first level childs
                first_level = dataset.filter(comment_level=1)
                save_data_to_JSON(first_level, doc, POPUP_OUTPUT)  # The complete graph is sent to the Main window

        # There is a subtree in the Main window
        if is_main_subtree:
            try:
                dataset_first_level, doc = get_current_dataset_popup(request, main_nodes, main_selected_item_popup)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            # The use of the 'save_data_to_JSON_popup' function indicates that a subtree is being generated.
            # The 'MAIN_OUTPUT' parameter indicates that the subtree is sent to the main window.
            save_data_to_JSON_popup(dataset_first_level, main_nodes, doc,
                                    MAIN_OUTPUT)  # The subtree is sent to the Main window

        # There is no subtree in the Main window
        else:
            try:
                dataset, doc = get_current_dataset(request, selected_item)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("document_not_exist")
            # Filter first level childs
            first_level = dataset.filter(comment_level=1)
            save_data_to_JSON(first_level, doc)  # The complete graph is sent to the Main window


def generate_dataset_popup(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', True):
        return HttpResponseBadRequest("open_document_no_active_session")

    # CURRENT ITEM
    # ---------------------------------------------------------------------------------
    if request.POST.get('popup_subtree_id'):
        popup_subtree = Subtree.objects.get(pk=request.POST["popup_subtree_id"])
        popup_nodes = popup_subtree.node_ids
        popup_selected_item = popup_subtree.document.description
    elif request.POST.get('popup_subtree_nodes_ids'):
        popup_nodes = list(map(int, request.POST['popup_subtree_nodes_ids'].split(",")))
        popup_selected_item = request.POST['popup_subtree_document_description']
    # ---------------------------------------------------------------------------------
    # JSON PARSING & CURRENT DATASET
    # ---------------------------------------------------------------------------------
    try:
        # Filter first level childs
        dataset_first_level, doc = get_current_dataset_popup(request, popup_nodes, popup_selected_item)
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("document_not_exist")
    save_data_to_JSON_popup(dataset_first_level, popup_nodes, doc)
    # ---------------------------------------------------------------------------------
    return HttpResponse("/static/output_popup.json")


@require_GET
def update_subtrees_menu(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    selected_item = request.GET["selected_item"]
    from_documents = request.GET["from_documents"]
    doc = Document.objects.filter(description=selected_item).first()

    if from_documents == 'all':
        user_subtrees = Subtree.objects.filter(user=user)
    elif from_documents == 'current':
        user_subtrees = Subtree.objects.filter(document=doc, user=user)
    else:
        user_subtrees = Subtree.objects.filter(user=user)

    return render(request, 'subtrees_menu.html', {'user_subtrees': user_subtrees})


def main_form_handler(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', True):
        return open_document_exception(request, "open_document_no_active_session")

    storage_clear = request.GET.get('storageClear', '')
    error_message = request.GET.get('chatbotError', '')
    if (error_message):
        error_message = get_chat_error_message(error_message)

    success_message = ''
    if request.POST.get('chatbot') == "true":
        if request.POST.get('changed_main_layout'):
            success_message = request.POST.get('from_chat_msg')
        else:
            success_message = "I have selected the best visualization according to the graph characteristics"

    try:
        selected_item, cbTargets, cbFeatures, cbFilterOR, cbFilterAND, cbCommons, selected_icons, selected_layout, template, checked_layout = main_form_context(
            request)
    except ObjectDoesNotExist:
        return open_document_exception(request, "document_not_exist")

    # Indicates whether the request is to work on the previous file,
    # for which the best display layout has already been selected.
    best_layout_selected = request.POST.get('best_layout_selected')
    if best_layout_selected == 'true':
        messages.success(request, "The best visualization according to the graph characteristics has been selected")

    context = {'dataset': MAIN_OUTPUT, 'options': get_all_documents(), 'layouts': LAYOUTS,
               'selected_layout': selected_layout,
               'checked_layout': checked_layout,
               'selected_item': selected_item,
               'selected_icons': selected_icons,
               # ? Uncomment this line in order to obtain the auxiliary_charts in visualization.
               # "d1": d1, "d2": d2,
               'cbTargets': cbTargets, 'cbFeatures': cbFeatures, 'cbFilterOR': cbFilterOR,
               'cbFilterAND': cbFilterAND, 'cbCommons': cbCommons, 'storage_clear': storage_clear,
               'chatbot_error': error_message, 'chatbot_success': success_message}

    # Default values
    context['main_hierarchy_name'] = request.POST["main_hierarchy_name"]
    context['main_layout_name'] = checked_layout
    context['selected_container'] = request.POST.get("selected_container", '')
    context['do_action'] = request.POST.get("do_action", '')

    main_graph_info = request.POST.get('main_graph_info', None)
    popup_graph_info = request.POST.get('popup_graph_info', None)

    action_popup = request.POST.get(
        'action_popup')  # Action to be performed in the Popup or Main window (swap, send_to_popup, send_to_main)
    if action_popup == "swap" or action_popup == "send_to_main" or (
            action_popup == "send_to_popup" and popup_graph_info):
        # Graph information in the main window
        context['main_graph_info'] = popup_graph_info
        context['main_subtree_nodes_ids'] = request.POST['popup_subtree_nodes_ids']
        context['main_subtree_document_description'] = request.POST['popup_subtree_document_description']
        context['main_subtree_name'] = request.POST["popup_subtree_name"]
        context['main_subtree_id'] = request.POST["popup_subtree_id"]
        context['main_hierarchy_name'] = request.POST["popup_hierarchy_name"]
        context['main_layout_name'] = request.POST["popup_layout_name"]

    if action_popup == "swap" or action_popup == "send_to_popup":
        # Graph information in the popup
        context['popup_graph_info'] = main_graph_info
        context['popup_dataset'] = POPUP_OUTPUT
        context['popup_subtree_nodes_ids'] = request.POST['main_subtree_nodes_ids']
        context['popup_subtree_document_description'] = request.POST['main_subtree_document_description']
        context['popup_subtree_name'] = request.POST["main_subtree_name"]
        context['popup_subtree_id'] = request.POST["main_subtree_id"]
        context['popup_hierarchy_name'] = request.POST["main_hierarchy_name"]
        context['popup_layout_name'] = request.POST["main_layout_name"]

    changed_main_layout = request.POST.get('changed_main_layout')
    if changed_main_layout:
        context['main_graph_info'] = main_graph_info
        context['main_subtree_nodes_ids'] = request.POST['main_subtree_nodes_ids']
        context['main_subtree_document_description'] = request.POST['main_subtree_document_description']
        context['main_subtree_name'] = request.POST["main_subtree_name"]
        context['main_subtree_id'] = request.POST["main_subtree_id"]
        context['main_hierarchy_name'] = request.POST["main_hierarchy_name"]
        context['main_layout_name'] = request.POST["main_layout_name"]

        # Graph information in the popup
        context['popup_graph_info'] = popup_graph_info
        context['popup_dataset'] = POPUP_OUTPUT
        context['popup_subtree_nodes_ids'] = request.POST['popup_subtree_nodes_ids']
        context['popup_subtree_document_description'] = request.POST['popup_subtree_document_description']
        context['popup_subtree_name'] = request.POST["popup_subtree_name"]
        context['popup_subtree_id'] = request.POST["popup_subtree_id"]
        context['popup_hierarchy_name'] = request.POST["popup_hierarchy_name"]
        context['popup_layout_name'] = request.POST["popup_layout_name"]

    return render(request, template, context=context)


def main_form_context(request):
    # CURRENT ITEM
    # ---------------------------------------------------------------------------------
    selected_item = Document.objects.first().description
    if "from_button" in request.POST.keys():
        selected_item = request.POST['from_button']
    if "selected_data" in request.POST.keys():
        selected_item = request.POST["selected_data"]
    # ---------------------------------------------------------------------------------

    # CHECKBOXES
    # ---------------------------------------------------------------------------------
    # Create two dicts that holds the values of the checkboxes from Targets and Features
    cbTargets = {target: 0 for target in TARGETS}
    cbFeatures = {feature: 0 for feature in FEATURES}
    cbFilterOR = {feature: 0 for feature in FILTERS}
    cbFilterAND = {feature: 0 for feature in FILTERS}
    cbCommons = {feature: 0 for feature in COMMONS}
    handle_checkboxes(request, cbTargets, cbFeatures, cbFilterOR, cbFilterAND, cbCommons)
    # ---------------------------------------------------------------------------------

    # ICONS
    # ---------------------------------------------------------------------------------
    selected_icons = handle_icons(request)
    # ---------------------------------------------------------------------------------

    # JSON PARSING & CURRENT DATASET
    # ---------------------------------------------------------------------------------
    auxiliar_generate_dataset(request, selected_item)
    # ---------------------------------------------------------------------------------

    selected_layout, template, checked_layout = get_selected_layout(request)

    # ? Uncomment this line in order to obtain the auxiliary_charts in visualization.
    # d1, d2 = auxiliary_charts(doc)

    return selected_item, cbTargets, cbFeatures, cbFilterOR, cbFilterAND, cbCommons, selected_icons, selected_layout, template, checked_layout


def open_document_exception(request, error):
    # Django Messages
    if (error == "document_not_exist"):
        errorMsg = "The document you want to open does not exist"

        request.POST = request.POST.copy()
        if "from_button" in request.POST.keys():
            request.POST['from_button'] = Document.objects.first().description
        if "selected_data" in request.POST.keys():
            request.POST["selected_data"] = Document.objects.first().description
    elif error == "open_document_no_active_session":
        errorMsg = "Log in to access the documents"
    else:
        errorMsg = "An error has occurred"

    if request.POST.get('chatbot') == "true":
        return get_template_by_path(request, error)
    else:
        messages.error(request, errorMsg)
        if error == "open_document_no_active_session":
            return redirect("index")
        else:
            if "from_button" in request.POST.keys():
                return redirect("index")
            elif "selected_data" in request.POST.keys():
                selected_item, cbTargets, cbFeatures, cbFilterOR, cbFilterAND, cbCommons, selected_icons, selected_layout, template, checked_layout = main_form_context(
                    request)

                return render(request, template,
                              {'dataset': MAIN_OUTPUT, 'options': get_all_documents(), 'layouts': LAYOUTS,
                               'selected_layout': selected_layout,
                               'checked_layout': checked_layout,
                               'selected_item': selected_item,
                               'selected_icons': selected_icons,
                               # ? Uncomment this line in order to obtain the auxiliary_charts in visualization.
                               # "d1": d1, "d2": d2,
                               'cbTargets': cbTargets, 'cbFeatures': cbFeatures, 'cbFilterOR': cbFilterOR,
                               'cbFilterAND': cbFilterAND, 'cbCommons': cbCommons})


# Auxiliary Form Handler functions
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
def handle_checkboxes(request, cbTargets, cbFeatures, cbFilterOR, cbFilterAND, cbCommons):
    if "cbTargets" in request.POST.keys():
        for target in request.POST.getlist("cbTargets"):
            cbTargets[target.replace('-', '_')] = 1
    if "cbFeatures" in request.POST.keys():
        for feature in request.POST.getlist("cbFeatures"):
            cbFeatures[feature] = 1
    if "cbFeatureMenu" in request.POST.keys():
        cbFeatures[request.POST["cbFeatureMenu"].replace('-', '_')] = 1
    if "cbHighlightOR" in request.POST.keys():
        for filterOR in request.POST.getlist("cbHighlightOR"):
            cbFilterOR[filterOR.replace('-', '_')] = 1
    if "cbHighlightAND" in request.POST.keys():
        for filterAND in request.POST.getlist("cbHighlightAND"):
            cbFilterAND[filterAND.replace('-', '_')] = 1
    if "cbHighlightProperty" in request.POST.keys():
        for common in request.POST.getlist("cbHighlightProperty"):
            cbCommons[common.replace('-', '_')] = 1
    else:
        cbCommons["and_group"] = 1


def get_current_dataset(request, selected_data):
    doc = Document.objects.filter(description=selected_data).first()
    if not (doc):
        raise ObjectDoesNotExist('document_not_exist')
    dataset = Commentary.objects.filter(document_id=doc).all()
    return dataset, doc


def get_current_dataset_popup(request, nodes, selected_data):
    doc = Document.objects.filter(description=selected_data).first()
    if not (doc):
        raise ObjectDoesNotExist('document_not_exist')
    dataset = Commentary.objects.filter(document_id=doc, comment_level=1, comment_id__in=nodes).all()
    return dataset, doc


def handle_icons(request):
    if "dots_icon_button" in request.POST.keys():
        return "dots"
    elif "glyphs_icon_button" in request.POST.keys():
        return "glyphs"
    elif "trivial_icon_button" in request.POST.keys():
        return "trivial"
    return "dots"


def get_result_node(node):
    return {
        "name": node.comment_id,
        "user_id": node.user_id,
        "date": node.date,
        "thread": node.thread,
        "comment_level": node.comment_level,
        "coment": node.comment,
        "argumentation": node.argumentation,
        "constructiveness": node.constructivity,
        "positive_stance": node.positive_stance,
        "negative_stance": node.negative_stance,
        "target_person": node.target_person,
        "target_group": node.target_group,
        "stereotype": node.stereotype,
        "sarcasm": node.sarcasm,
        "mockery": node.mockery,
        "insult": node.insult,
        "improper_language": node.improper_language,
        "aggressiveness": node.aggressiveness,
        "intolerance": node.intolerance,
        "toxicity": node.toxicity,
        "toxicity_level": node.toxicity_level,
    }


def recursive_add_node(node, doc):
    result = get_result_node(node)
    children = [recursive_add_node(c, doc) for c in
                Commentary.objects.filter(document_id=doc).all().filter(thread=node.comment_id, comment_level=2)]
    if children:
        result["children"] = children
    return result


def recursive_add_node_popup(node, nodes, doc):
    result = get_result_node(node)
    children = [recursive_add_node_popup(c, nodes, doc) for c in
                Commentary.objects.filter(document_id=doc).all().filter(thread=node.comment_id, comment_level=2)
                if c.comment_id in nodes]
    if children:
        result["children"] = children
    return result


def save_data_to_JSON(first_level, doc, output_file=MAIN_OUTPUT):
    # Recursivamente añadimos sus hijos.
    data_list = [recursive_add_node(node, doc) for node in first_level]

    data = {"name": doc, "title": doc.title, "text_URL": doc.text_URL, "comments_URL": doc.comments_URL,
            "children": data_list}
    with open(os.path.join('DataVisualization/' + django_settings.STATIC_URL, output_file), 'w') as outfile:
        json.dump(data, outfile, default=str)


def save_data_to_JSON_popup(first_level, nodes, doc, output_file=POPUP_OUTPUT):
    # Recursivamente añadimos sus hijos.
    data_list = [recursive_add_node_popup(node, nodes, doc) for node in first_level]

    data = {"name": doc, "title": doc.title, "text_URL": doc.text_URL, "comments_URL": doc.comments_URL,
            "children": data_list}
    with open(os.path.join('DataVisualization/' + django_settings.STATIC_URL, output_file), 'w') as outfile:
        json.dump(data, outfile, default=str)


def get_selected_layout(request):
    action_popup = request.POST.get(
        'action_popup')  # Action to be performed in the Popup or Main window (swap, send_to_popup, send_to_main)
    main_layout_name = request.POST.get('main_layout_name')
    popup_graph_info = request.POST.get('popup_graph_info', None)
    if action_popup == "swap" or action_popup == "send_to_main" or (
            action_popup == "send_to_popup" and popup_graph_info):
        selected_layout = request.POST["popup_layout_name"] + "_layout.html"
        template = request.POST["popup_layout_name"] + "_layout.html"
        button_checked = request.POST["popup_layout_name"]
    elif main_layout_name:
        selected_layout = request.POST["main_layout_name"] + "_layout.html"
        template = request.POST["main_layout_name"] + "_layout.html"
        button_checked = request.POST["main_layout_name"]
    elif TREE_LAYOUT in request.POST.keys():
        selected_layout = "tree_layout.html"
        template = "tree_layout.html"
        button_checked = "tree"
    elif FORCE_LAYOUT in request.POST.keys():
        selected_layout = "force_layout.html"
        template = "force_layout.html"
        button_checked = "force"
    elif RADIAL_LAYOUT in request.POST.keys():
        selected_layout = "radial_layout.html"
        template = "radial_layout.html"
        button_checked = "radial"
    elif CIRCLE_LAYOUT in request.POST.keys():
        selected_layout = "circle_layout.html"
        template = "circle_layout.html"
        button_checked = "circle"
    else:
        selected_layout = "tree_layout.html"
        template = "tree_layout.html"
        button_checked = "tree"

    return selected_layout, template, button_checked


def auxiliary_charts(doc):
    # Auxiliary charts
    # ----------------
    d1 = Commentary.objects.filter(document_id=doc) \
        .values('toxicity') \
        .annotate(toxicity_no=Count('toxicity', filter=Q(toxicity=0))) \
        .annotate(toxicity_yes=Count('toxicity', filter=Q(toxicity=1))) \
        .annotate(low_toxicity=Count('toxicity_level', filter=Q(toxicity_level=1))) \
        .annotate(med_toxicity=Count('toxicity_level', filter=Q(toxicity_level=2))) \
        .annotate(high_toxicity=Count('toxicity_level', filter=Q(toxicity_level=3)))

    d2 = Commentary.objects.filter(document_id=doc) \
        .values('toxicity') \
        .annotate(sarcasm=Count('sarcasm', filter=Q(sarcasm=1))) \
        .annotate(argumentation=Count('argumentation', filter=Q(argumentation=1))) \
        .annotate(positive_stance=Count('positive_stance', filter=Q(positive_stance=1))) \
        .annotate(negative_stance=Count('negative_stance', filter=Q(negative_stance=1)))
    # ----------------
    return d1, d2


# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------


# Manage Data functions
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
def upload_file(request):
    if request.method == 'POST':
        file_form = FileForm(request.POST, request.FILES)
        if file_form.is_valid():
            handle_uploaded_file(request.FILES['document'])
            file_form.save()
            parse_data(Document.objects.last())
            messages.success(request, "Document has been uploaded correctly")
            return index(request)
        else:
            messages.error(request, "The form received is not valid")
            file_form = FileForm()
            return render(request, "upload_file.html",
                          context={'form': file_form, 'documents_uploaded': get_all_documents()})
    else:
        error_message = request.GET.get('chatbotError', '')
        if (error_message):
            error_message = get_chat_error_message(error_message)
        file_form = FileForm()
        return render(request, "upload_file.html",
                      context={'form': file_form, 'documents_uploaded': get_all_documents(), 'chatbot_error': error_message})


def handle_uploaded_file(f):
    with open('DataVisualization/static/' + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def create_subtree(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', True):
        return HttpResponseBadRequest("create_subtree_no_active_session")

    selected_item = request.POST["selected_item"]
    doc = Document.objects.filter(description=selected_item).first()
    if not (doc):
        raise ObjectDoesNotExist('create_subtree_document_not_exist')

    node_ids = list(map(int, request.POST["node_ids"].split(",")))
    subtree_name = request.POST["subtree_name"]

    # Check if the user already has this subtree associated with it
    if Subtree.objects.filter(document=doc, user=user, node_ids=node_ids).exists():
        return HttpResponseBadRequest("subtree_already_exists")
    # Checks if there is already a subtree with that name for that user
    if Subtree.objects.filter(user=user, name=subtree_name).exists():
        return HttpResponseBadRequest("name_already_exists")

    new_subtree = Subtree.objects.create(name=subtree_name, document=doc, user=user, node_ids=node_ids)

    return HttpResponse(new_subtree.pk)


def delete_subtree(request, subtree_id):
    Subtree.objects.filter(subtree_id=subtree_id).delete()
    return HttpResponse(status=204)


def edit_data(request, document_id):
    document = Document.objects.get(pk=document_id)
    form = UpdateFileForm(request.POST or None, instance=document)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Document has been updated correctly")
            return index(request)
        else:
            messages.error(request, "The form received is not valid")
            return render(request, "upload_file.html",
                          context={'form': form, 'documents_uploaded': get_all_documents()})
    else:
        error_message = request.GET.get('chatbotError', '')
        if (error_message):
            error_message = get_chat_error_message(error_message)
        return render(request, 'update_file.html',
                      {'documents_uploaded': get_all_documents(), 'document': document, 'form': form, 'chatbot_error': error_message})


def handle_delete_data(request):
    try:
        selected_data = request.POST["delete_button"]
    except MultiValueDictKeyError as e:
        selected_data = Document.objects.first()
    delete_data(selected_data)
    return index(request)


def manage_data(request):
    if request.method == 'POST':
        handle_delete_data(request)
    if request.GET.get("save_button"):
        save_project()
    if request.GET.get("export_button"):
        export_visualization()
    return index(request)


def parse_data(document):
    parser = ExcelParser()
    parser.load_and_parse(Document.objects.filter(
        description=document.description).first())


def delete_data(selected_data):
    parser = ExcelParser()
    parser.drop_database(selected_data)


def save_project():
    raise NotImplementedError()


def export_visualization():
    raise NotImplementedError()


# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

from django.shortcuts import render, redirect, reverse
from .forms import Loginform
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def login_view(request):
    storage_clear = request.GET.get('storageClear', '')
    error_message = request.GET.get('chatbotError', '')
    if (error_message):
        error_message = get_chat_error_message(error_message)

    if request.POST.get('username') and request.POST.get('password') and request.POST.get('chatbot') == "true":
        request = decrypt_login_params(request)

    form = Loginform(request.POST or None)

    if request.POST.get('username') and request.POST.get('password') and request.POST.get('chatbot') == "true":
        return login_process(request, form, request.POST.get('username'), request.POST.get('password'))

    elif form.is_valid():
        uservalue = form.cleaned_data.get('username')
        passwordvalue = form.cleaned_data.get('password')

        return login_process(request, form, uservalue, passwordvalue)
    else:
        context = {'form': form, 'storage_clear': storage_clear, 'chatbot_error': error_message}
        return render(request, 'login.html', context)


def decrypt_login_params(request):
    key = b'ZeuY3kEaYn2XkyPQPQKgDmDeDRJfKYM3-tTx_5NmMm4='
    request.POST = request.POST.copy()
    request.POST['username'] = decrypt(str.encode(request.POST.get('username')), key).decode()
    request.POST['password'] = decrypt(str.encode(request.POST.get('password')), key).decode()
    return request


def login_process(request, form, uservalue, passwordvalue):
    user = authenticate(username=uservalue, password=passwordvalue)
    if user is not None and request.user.get_username() != user.get_username():
        login(request, user)
        if request.POST.get('chatbot') == "true":
            return storage_clear_index(request, 'login')
        else:
            return storage_clear_index(request, 'nochat')
    elif user is not None and request.user.get_username() == user.get_username():
        return login_exception(request, "same_username", form)
    else:
        return login_exception(request, "bad_credentials", form)


def login_exception(request, error, form):

    if request.POST.get('chatbot') == "true":
        return get_template_by_path(request, error)
    else:
        # Django Messages
        if error == "same_username":
            messages.error(request, "Attempting to log in as the current user")
        elif error == "bad_credentials":
            messages.error(request, "The username and password combination is incorrect")
        else:
            messages.error(request, 'An error has occurred')
        return render(request, 'login.html', context={'form': form})


def signup_view(request):
    storage_clear = request.GET.get('storageClear', '')
    error_message = request.GET.get('chatbotError', '')
    if (error_message):
        error_message = get_chat_error_message(error_message)

    if request.method == 'POST':
        if request.POST.get('username') and request.POST.get('password1') and request.POST.get(
                'password2') and request.POST.get('chatbot') == "true":
            request = decrypt_signup_params(request)

        form = UserCreationForm(request.POST)

        if (User.objects.filter(username=request.POST.get('username')).exists()):
            return signup_exception(request, "username_already_exists", form)
        elif (request.POST.get('password1') != request.POST.get('password2')):
            return signup_exception(request, "passwords_not_match", form)

        message_text = "The user has been created successfully"
        if not request.POST.get('chatbot') == "true":
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, message_text)
                return storage_clear_index(request, 'nochat')
        else:
            user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
            login(request, user)
            messages.success(request, message_text)
            return storage_clear_index(request, 'signup')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html',
                  context={'form': form, 'storage_clear': storage_clear, 'chatbot_error': error_message})


def decrypt_signup_params(request):
    key = b'JlgbJKpxVhwF3NXJf_n-lt4c4AvdCATnuXYDK4xivPY='
    request.POST = request.POST.copy()
    request.POST['username'] = decrypt(str.encode(request.POST.get("username")), key).decode()
    request.POST['password1'] = decrypt(str.encode(request.POST.get("password1")), key).decode()
    request.POST['password2'] = decrypt(str.encode(request.POST.get("password2")), key).decode()

    return request


def signup_exception(request, error, form):

    if request.POST.get('chatbot') == "true":
        return get_template_by_path(request, error)
    else:
        # Django Messages
        if error == "passwords_not_match":
            messages.error(request, "The two passwords provided do not match")
        elif (error == "username_already_exists"):
            messages.error(request, "A user with that username already exists")
        else:
            messages.error(request, "An error has occurred")
        return render(request, 'signup.html', context={'form': form})


def logout_view(request):
    # Check if there is an active session
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', True):
        response = logout_exception(request, "logout_no_active_session")
    else:
        logout(request)
        messages.success(request, "Your session has been successfully closed")
        if (request.GET.get("chatbot") == "true"):
            response = storage_clear_index(request, 'logout')
        else:
            response = storage_clear_index(request, 'nochat')

    return response


def logout_exception(request, error):
    if request.GET.get("chatbot") == "true":
        return get_template_by_path(request, error)
    else:
        messages.error(request, "No active session detected to be closed")
        return redirect(reverse('index'))


def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)


def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


def get_template_by_path(request, error_message):
    path_prev_url = urlparse(request.META['HTTP_REFERER']).path.split('/')
    viewname = path_prev_url[1]

    if viewname == "" or viewname == "logout":
        return redirect(reverse('index') + '?chatbotError=' + error_message)

    elif viewname == "selected_data":
        if (error_message == "open_document_no_active_session"):
            return redirect(reverse('index') + '?chatbotError=' + error_message)
        else:
            if request.method == 'POST':
                inject_text_conversation(request.POST["session_id"], get_chat_error_message(error_message))
            elif request.method == 'GET':
                inject_text_conversation(request.GET["session_id"], get_chat_error_message(error_message))

            return HttpResponse(status=204)

    elif viewname == "edit_data":
        return redirect(reverse(viewname, kwargs={'document_id':path_prev_url[2]}) + '?chatbotError=' + error_message)
    else:
        return redirect(reverse(viewname) + '?chatbotError=' + error_message)


def get_chat_error_message(errorName):
    messages_dict = {'same_username': "The username you have given me matches the username of your current session",
                'bad_credentials': "The username and password combination you have given me is not valid",
                'passwords_not_match': "I have not been able to register the user, the two passwords you have given me do not match",
                'username_already_exists': "I have not been able to register the user, there is already a user with this name",
                'logout_no_active_session': "It is not possible to close a session that does not exist, you are not logged in...",
                'document_not_exist': "I cannot find any document with the name you have given me",
                'open_document_no_active_session': "You need to be logged in to access the documents", }
    if errorName in messages_dict:
        return messages_dict[errorName]
    else:
        return "An error has occurred"


def get_chat_success_message(request, successName):
    messages_dict = {'best_layout': "I have selected the best visualization according to the graph characteristics"}
    return messages_dict[successName]


def inject_text_conversation(session_id, textMsg):
    url = 'http://datavisualizationinlinguistics.herokuapp.com:5005/conversations/' + session_id + '/trigger_intent?token=DataVisualizationInLinguisticsSecretToken&include_events=NONE&output_channel=socketio'
    json_msg = {
        "name": "generate_response_message",
        "entities": {
            "response_message": textMsg
        }
    }
    requests.post(url, json=json_msg)
