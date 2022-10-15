// Variable to check if the ready function code has been completely executed
var codeReady = false;

let svg = d3.select("#svg_treeMap")
//let svg = d3
        //.select("#whole-container")
        //.append("svg")
        //.attr("width", 960)
        //.attr("height", 960)


    let diameter = svg.attr("width"),
    g = svg.append("g").attr("transform", "translate(2,2)"),
    format = d3.format(",d");

let pack = d3.pack()
    .size([diameter - 2, diameter - 2])
    .padding(3);

var tooltipText;

 // Hover rectangle in which the information of a node is displayed
var tooltip = d3.select("#circletree-container")
    .append("div")
    .attr("class", "my-tooltip") //add the tooltip class
    .style("position", "absolute")
    .style("z-index", "60")
    .style("visibility", "hidden");

var node;

var root;

const colourToxicity0 = "#f7f7f7", colourToxicity1 = "#cccccc", colourToxicity2 = "#737373",
    colourToxicity3 = "#000000", colourNewsArticle = "#C8EAFC";

const minOpacityValue = 0.2, maxOpacityValue = 1;

// shadow filter //
const defs = svg.append("defs");

let filter = defs.append("filter")
    .attr("id", "dropshadow")

filter.append("feDropShadow")
    .attr("flood-opacity", 1)
    .attr("dx", 0)
    .attr("dy", 1)


// Select which properties and if an intersection or union of those
// let checkboxHighlightMenu = document.querySelector("input[name=cbHighlightMenu]");

let checkboxesProperty = document.querySelectorAll("input[type=checkbox][name=cbHighlightProperty]");
let checkboxAND = document.querySelector("input[type=radio][name=cbHighlightProperty][value=and-group]");
let checkboxOR = document.querySelector("input[type=radio][name=cbHighlightProperty][value=or-group]");
var checkboxesHighlightGroupOR = document.querySelectorAll("input[type=checkbox][name=cbHighlightOR]");
var checkboxesHighlightGroupAND = document.querySelectorAll("input[type=checkbox][name=cbHighlightAND]");

console.log('[User]', user.split('/')[2], '| [interaction]', 'TreeMap_layout_loaded', '| [Date]', Date.now());
var enabledHighlight = []; //Variable which contains the string of the enabled options to highlight
treeJSON = d3.json(dataset, function (error, root) {

        /*SECTION checkboxes*/
    //Check the values of the checkboxes and do something
    var checkbox = document.querySelector("input[name=cbTargets]");
    var checkboxesTargets = [document.getElementById("target-group"), document.getElementById("target-person"), document.getElementById("target-stereotype")];
    let enabledTargets = []; //Variable which contains the string of the enabled options to display targets

    // Select all checkboxes with the name 'cbFeatures' using querySelectorAll.
    var checkboxes = document.querySelectorAll("input[type=checkbox][name=cbFeatures]");
    let enabledFeatures = []; //Variable which contains the string of the enabled options to display features

    // Select how to display the features: svg circles or trivial cheese (previous version)
    var checkboxesPropertyFeature = document.querySelectorAll("input[type=checkbox][name=cbFeatureProperty]");

    //Dropdown menu
    var checkboxesPositioningFeature = document.querySelectorAll("input[type=checkbox][name=cbFeaturePositioning]");

    // Select which properties and if an intersection or union of those
    var checkboxesProperty = document.querySelectorAll("input[type=checkbox][name=cbHighlightProperty]");
    var checkboxAND = document.querySelector("input[type=radio][name=cbHighlightProperty][value=and-group]");
    var checkboxOR = document.querySelector("input[type=radio][name=cbHighlightProperty][value=or-group]");
    var checkboxesHighlightGroupOR = document.querySelectorAll("input[name=cbHighlightOR]");
    var checkboxesHighlightGroupAND = document.querySelectorAll("input[name=cbHighlightAND]");

    let enabledHighlight = []; //Variable which contains the string of the enabled options to highlight

    if (error) throw error;


    root = d3.hierarchy(root)
        .sum(function (d) {
            switch (d.comment_level) {
                //case 0:
                //return colourToxicity0;
                case 1:
                    return 15;
                case 2:
                    return 8;
                default:
                    return 5;
            }
        })
        .sort(function (a, b) {
            return b.comment_level - a.comment_level;
        });

    var node = g.selectAll(".node")
        .data(pack(root).descendants())
        .enter().append("g")
        .attr("class", function (d) {
            return d.children ? "node" : "leaf node";
        })
        .attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        })


    //node.append("title")
    //  .text(function(d) { return d.data.name + "\n" + format(d.value); });
    //
    node.append("circle")
        .attr("r", function (d) {
            if (d.depth === 0) {
                return d.r;
            }
            if (d.children) {
                if (d.children.length === 1) {
                    // return ((d.r + ((d.r * (1 / d.depth)))));
                    return d.r + (d.r * (0.3 / d.depth));

                } else {
                    return d.r;
                }
            } else {
                return d.r;
            }
        })
        .attr("filter", "url(#dropshadow)")
        .style("fill", function (d) {
            if (d.data.toxicity_level === 0) return colourToxicity0;
            else {
                switch (d.data.toxicity_level) {
                    //case 0:
                    //return colourToxicity0;
                    case 1:
                        return colourToxicity1;
                    case 2:
                        return colourToxicity2;
                    case 3:
                        return colourToxicity3;
                    default:
                        return colourNewsArticle;
                }
            }
        }).style("stroke", "black")
          .on("mouseover", function (d) {
                if (d !== root) {
                    writeTooltipText(d.data, d.depth);
                    tooltip.style("visibility", "visible").html(tooltipText);
                } else {
                    writeTooltipRoot(d.data, d.depth);
                    tooltip.style("visibility", "visible").html(tooltipText);
                }
            })
        .on("mousemove", function (d) {
                // if (d !== root) {
                    return tooltip.style("top", (d3.mouse(document.querySelector("#circletree-container"))[1] + 60) + "px").style("left", (d3.mouse(document.querySelector("#circletree-container"))[0] + 65) + "px");
                // }
            })
        .on("mouseout", function () {
                return tooltip.style("visibility", "hidden");
            });
        //    .on("mouseover", function(d){  console.log(d)
        //        return tooltip.text(d.data.name).style("visibility", "visible").html("tooltip");})
        //    .on("mousemove", function(){return tooltip.style("top", d3.event.pageY -30 +"px").style("left",d3.event.pageX + 480 +"px");})
	    //    .on("mouseout", function(){return tooltip.style("visibility", "hidden");});

/**
 * Recursive function to compute the global statistics
 * counts nodes by toxicity and by targets
 * */
function getStatisticValues(node) {
    if (!node.children) {
        return {
            children: 0,
            toxicityLevel: node.data.toxicity_level,
            toxicity0: 0,
            toxicity1: 0,
            toxicity2: 0,
            toxicity3: 0,
            totalTargGroup: 0,
            totalTargPerson: 0,
            totalTargStereotype: 0,
            totalTargNone: 0,
            targGroup: node.data.target_group,
            targPerson: node.data.target_person,
            targStereotype: node.data.stereotype,
            targNone: 0
        };
    }
    var total = 0, childrenList = [],
        totalToxic0 = 0, totalToxic1 = 0, totalToxic2 = 0, totalToxic3 = 0,
        totalTargGroup = 0, totalTargPerson = 0, totalTargStereotype = 0, totalTargNone = 0;

    if (node.children) {
        node.children.forEach(function (d) {
            childrenList = getStatisticValues(d);
            total += childrenList.children + 1;

            totalToxic0 += childrenList.toxicity0;
            totalToxic1 += childrenList.toxicity1;
            totalToxic2 += childrenList.toxicity2;
            totalToxic3 += childrenList.toxicity3;

            switch (childrenList.toxicityLevel) {

                case 0:
                    totalToxic0 += 1;
                    break;

                case 1:
                    totalToxic1 += 1;
                    break;

                case 2:
                    totalToxic2 += 1;
                    break;

                case 3:
                    totalToxic3 += 1;
                    break;
            }

            //Targets are not exclusive
            childrenList.targGroup ? totalTargGroup += childrenList.totalTargGroup + 1 : totalTargGroup += childrenList.totalTargGroup;
            childrenList.targPerson ? totalTargPerson += childrenList.totalTargPerson + 1 : totalTargPerson += childrenList.totalTargPerson;
            childrenList.targStereotype ? totalTargStereotype += childrenList.totalTargStereotype + 1 : totalTargStereotype += childrenList.totalTargStereotype;
            (!childrenList.targGroup && !childrenList.targPerson && !childrenList.targStereotype) ? totalTargNone += childrenList.totalTargNone + 1 : totalTargNone += childrenList.totalTargNone;
        })
    }

    return {
        children: total,
        toxicityLevel: node.data.toxicity_level,
        toxicity0: totalToxic0,
        toxicity1: totalToxic1,
        toxicity2: totalToxic2,
        toxicity3: totalToxic3,
        totalTargGroup: totalTargGroup,
        totalTargPerson: totalTargPerson,
        totalTargStereotype: totalTargStereotype,
        totalTargNone: totalTargNone,
        targGroup: node.data.target_group,
        targPerson: node.data.target_person,
        targStereotype: node.data.stereotype,
        targNone: 0
    };
}

//I compute the values for the statistic data showing in the background
var listStatistics = getStatisticValues(root);
var totalNumberOfNodes = listStatistics.children;

var totalNotToxic = listStatistics.toxicity0,
    totalMildlyToxic = listStatistics.toxicity1,
    totalToxic = listStatistics.toxicity2,
    totalVeryToxic = listStatistics.toxicity3;

function writeTooltipRoot(d) {

    var sonTitles = [
        "Direct comments",
        "Total number of generated comments",
        "Not toxic",
        "Mildly toxic",
        "Toxic",
        "Very toxic",
    ];
    var sonValues = [
        d.children ? d.children.length : null,
        totalNumberOfNodes,
        totalNotToxic,
        totalMildlyToxic,
        totalToxic,
        totalVeryToxic,
    ];
    tooltipText = "<table>";
    tooltipText += "<table>";

    for (i = 0; i < sonValues.length; i++) {
        if (i % 2 === 0) tooltipText += "<tr>"; //Start table line
        tooltipText +=
            "<td>" + sonTitles[i] + ": " + sonValues[i] + "</td>";
        if ((i + 1) % 2 === 0) tooltipText += "</tr>"; //End table line
    }

    tooltipText += "<br> <table>";
}

function writeTooltipText(d, depth) {
    //I want to show Argument and Constructiveness in one line, I add a dummy space to keep that in the loop
    var jsonValues = [
        d.name,
        d.toxicity_level,
        depth,
        d.argumentation,
        d.constructiveness,
        -1,
        d.sarcasm,
        d.mockery,
        d.intolerance,
        d.improper_language,
        d.insult,
        d.aggressiveness,
        d.target_group,
        d.target_person,
        d.stereotype,
    ];
    var jsonNames = [
        "Comment ID",
        "Toxicity level",
        "Comment depth",
        "Argument",
        "Constructiveness",
        " ",
        "Sarcasm",
        "Mockery",
        "Intolerance",
        "Improper language",
        "Insult",
        "Aggressiveness",
        "Target group",
        "Target person",
        "Stereotype",
    ];
    var i = 0;
    tooltipText = "<table>";

    for (i = 0; i < jsonValues.length; i++) {
        if (i === 3 || i === 12) tooltipText += "<tr><td></td></tr>"; // I want a break between the first line and the features and the targets
        if (i % 3 === 0) tooltipText += "<tr>"; //Start table line
        if (i < 3)
            tooltipText +=
                "<td>" + jsonNames[i] + ": " + jsonValues[i] + "</td>";
        //First ones without bold
        else if (jsonValues[i] !== -1)
            jsonValues[i] ?
                (tooltipText +=
                    "<td><b>" +
                    jsonNames[i] +
                    ": " +
                    jsonValues[i] +
                    "</b></td>") :
                (tooltipText +=
                    "<td>" + jsonNames[i] + ": " + jsonValues[i] + "</td>");
        if ((i + 1) % 3 === 0) tooltipText += "</tr>"; //End table line
    }

    tooltipText += "</table>";

    tooltipText += "<br> <table>";
    //If node is collapsed, we also want to add some information about its sons
    if (d._children) {
       var sonTitles = [
           "Direct comments",
           "Total number of generated comments",
           "Not toxic",
            "Mildly toxic",
            "Toxic",
            "Very toxic",
        ];
        var sonValues = [
            d._children.length,
            d.numberOfDescendants,
            d.descendantsWithToxicity0,
            d.descendantsWithToxicity1,
            d.descendantsWithToxicity2,
            d.descendantsWithToxicity3,
        ];

        for (i = 0; i < sonValues.length; i++) {
            if (i % 2 === 0) tooltipText += "<tr>"; //Start table line
            tooltipText +=
                "<td>" + sonTitles[i] + ": " + sonValues[i] + "</td>";
            if ((i + 1) % 2 === 0) tooltipText += "</tr>"; //End table line
        }
    }
    tooltipText += "</table>";
    tooltipText += "<br>" + d.coment;
 }

function hovered(hover) {
    return function(d) {
        d3.selectAll(d.ancestors().map(function(d) {}));
  };
}

//Functions to highlight/unhighlight
function highlightNodesByPropertyOR(node, enabledHighlight) {
    //If no tag (toxicity, stance,...) checkbox is selected: highlight all
    if (enabledHighlight.length === 0) {
        node.style("opacity", maxOpacityValue);
    } else { //If some tag checkbox is selected behave as expected
        //First, unhighlight everything
        node.style("opacity", minOpacityValue);

        //Then highlight if the node has the property
        highlightByToxicity(node, enabledHighlight, highlightNode);
        highlightByFeature(node, enabledHighlight, highlightNode);
        highlightByStance(node, enabledHighlight, highlightNode);
        highlightByTarget(node, enabledHighlight, highlightNode);
    }
    node.filter(function (d) {
        return d.depth === 0;
    }).style("opacity", maxOpacityValue);

}

function highlightNodesByPropertyAND(node, enabledHighlight) {
    //First, highlight everything
    node.style("opacity", maxOpacityValue);

    //Then unhighlight if the node does not have the property
    highlightByToxicity(node, enabledHighlight, unhighlightNode);
    highlightByFeature(node, enabledHighlight, unhighlightNode);
    highlightByStance(node, enabledHighlight, unhighlightNode);
    highlightByTarget(node, enabledHighlight, unhighlightNode);
    node.filter(function (d) {
        return d.depth === 0;
    }).style("opacity", maxOpacityValue);

}

    try {
        $(document).ready(function () {
            checkboxAND.addEventListener("change", function () {
                if (this.checked) {
                    checkboxOR.checked = false;

                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupAND) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.
                    highlightNodesByPropertyAND(node, enabledHighlight);
                } else {
                    checkboxOR.checked = true;
                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupOR) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.

                    highlightNodesByPropertyOR(node, enabledHighlight);
                }
            });
// If OR is selected, uncheck the AND and highlight by property OR
            checkboxOR.addEventListener("change", function () {
                if (this.checked) {
                    checkboxAND.checked = false;

                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupOR) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.
                    highlightNodesByPropertyOR(node, enabledHighlight);
                } else {
                    checkboxAND.checked = true;
                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupAND) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.

                    highlightNodesByPropertyAND(node, enabledHighlight);
                }
            });

// Use Array.forEach to add an event listener to each checkbox.
            checkboxesHighlightGroupOR.forEach(function (checkboxItem) {
                checkboxItem.addEventListener('change', function () {
                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupOR) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.


                    var filteredOriginalToxicity = getLengthFilterByName(Array.from(checkboxesHighlightGroupOR).map(i => i.value), "highlight-toxicity-");
                    var filteredCompareToxicity = getLengthFilterByName(Array.from(enabledHighlight), "highlight-toxicity-");
                    document.getElementById('highlight-OR-selectAll-toxicity').checked = filteredOriginalToxicity === filteredCompareToxicity;

                    var filteredOriginalStance = getLengthFilterByName(Array.from(checkboxesHighlightGroupOR).map(i => i.value), "highlight-stance-");
                    var filteredCompareStance = getLengthFilterByName(Array.from(enabledHighlight), "highlight-stance-");
                    document.getElementById('highlight-OR-selectAll-stance').checked = filteredOriginalStance === filteredCompareStance;

                    var filteredOriginalTarget = getLengthFilterByName(Array.from(checkboxesHighlightGroupOR).map(i => i.value), "highlight-target-");
                    var filteredCompareTarget = getLengthFilterByName(Array.from(enabledHighlight), "highlight-target-");
                    document.getElementById('highlight-OR-selectAll-target').checked = filteredOriginalTarget === filteredCompareTarget;

                    var filteredOriginalFeatures = getLengthFilterByName(Array.from(checkboxesHighlightGroupOR).map(i => i.value), "highlight-features-");
                    var filteredCompareFeatures = getLengthFilterByName(Array.from(enabledHighlight), "highlight-features-");
                    document.getElementById('highlight-OR-selectAll-features').checked = filteredOriginalFeatures === filteredCompareFeatures;

                    if (checkboxItem.checked) {
                        console.log("[User]", user.split('/')[2], "| [interaction]", "checking_" + checkboxItem.name + '_' + checkboxItem.value, "| [Date]", Date.now());
                    } else {
                        console.log("[User]", user.split('/')[2], "| [interaction]", "unchecking_" + checkboxItem.name + '_' + checkboxItem.value, " | [Date]", Date.now());
                    }
                    checkboxOR.checked ? highlightNodesByPropertyOR(node, enabledHighlight) : highlightNodesByPropertyAND(node, enabledHighlight);
                })
            });

// Use Array.forEach to add an event listener to each checkbox.
            checkboxesHighlightGroupAND.forEach(function (checkboxItem) {
                checkboxItem.addEventListener('change', function () {
                    enabledHighlight =
                        Array.from(checkboxesHighlightGroupAND) // Convert checkboxes to an array to use filter and map.
                            .filter(i => i.checked) // Use Array.filter to remove unchecked checkboxes.
                            .map(i => i.value) // Use Array.map to extract only the checkbox values from the array of objects.

                    var filteredOriginalTarget = getLengthFilterByName(Array.from(checkboxesHighlightGroupAND).map(i => i.value), "highlight-target-");
                    var filteredCompareTarget = getLengthFilterByName(Array.from(enabledHighlight), "highlight-target-");
                    document.getElementById('highlight-AND-selectAll-target').checked = filteredOriginalTarget === filteredCompareTarget;

                    var filteredOriginalFeatures = getLengthFilterByName(Array.from(checkboxesHighlightGroupAND).map(i => i.value), "highlight-features-");
                    var filteredCompareFeatures = getLengthFilterByName(Array.from(enabledHighlight), "highlight-features-");
                    document.getElementById('highlight-AND-selectAll-features').checked = filteredOriginalFeatures === filteredCompareFeatures;

                    if (checkboxItem.checked) {
                        console.log("[User]", user.split('/')[2], "| [interaction]", "checking_" + checkboxItem.name + '_' + checkboxItem.value, " | [Date]", Date.now());
                    } else {
                        console.log("[User]", user.split('/')[2], "| [interaction]", "unchecking_" + checkboxItem.name + '_' + checkboxItem.value, " | [Date]", Date.now());
                    }
                    checkboxAND.checked ? highlightNodesByPropertyAND(node, enabledHighlight) : highlightNodesByPropertyOR(node, enabledHighlight);
                })
            });

            // To notify the DOM that the ready function has finished executing.
            // This to be able to manage the filters if it is given the case that the code of the onLoad function finishes before.
            const event = new Event('codeReady');

            // Dispatch the event.
            document.querySelector("body").dispatchEvent(event);

            codeReady = true;
        });
    } catch
        (TypeError) {
        console.error("Error attaching buttons... trying again...");
    }
    highlightNodesByPropertyOR(node, enabledHighlight);
    highlightNodesByPropertyAND(node, enabledHighlight);


    //Listeners

//Listener related to highlighting nodes and edges
// checkboxHighlightMenu.addEventListener('change', function () {
//     if (this.checked) {
//         checkboxesProperty.forEach(function (checkboxItem) {
//             checkboxItem.removeAttribute('disabled');
//         });
//         checkboxesHighlightGroup.forEach(function (checkboxItem) {
//             checkboxItem.removeAttribute('disabled');
//         });
//
//         if (!document.querySelector("input[value=and-group]").checked && !document.querySelector("input[value=or-group]").checked) {
//             document.querySelector("input[value=and-group]").checked = true;
//             highlightNodesByPropertyAND(node);
//         } else {
//             checkboxAND.checked ? highlightNodesByPropertyAND(node, enabledHighlight) : highlightNodesByPropertyOR(node, enabledHighlight);
//             console.log(enabledHighlight);
//         }
//
//     } else {
//         console.log("We disable all checkboxes ...");
//         checkboxesProperty.forEach(function (checkboxItem) {
//             checkboxItem.setAttribute('disabled', 'disabled');
//         });
//         checkboxesHighlightGroup.forEach(function (checkboxItem) {
//             checkboxItem.setAttribute('disabled', 'disabled');
//         });
//
//         //We make all nodes and links visible again
//         node.style("opacity", 1);
//         //link.style("opacity", 1);
//     }
// });

// If AND is selected, uncheck the OR and highlight by property AND

    function getLengthFilterByName(array, stringToMatch, matchPositive = true) {
        return Array.from(array).filter(function (val) {
            if (matchPositive) {
                return val.includes(stringToMatch);
            } else {
                return !val.includes(stringToMatch);
            }
        }).length;
    }


    /**
     * Return the value of a property (set from the JSON) of the given node
     *
     * @param d Datum of a node
     * @param {string} propertyNameToRetrieve The property whose value is returned
     * */
    function retrieveAttributeFromComment(d, propertyNameToRetrieve) {
        switch (propertyNameToRetrieve) {
            //Features
            case "argumentation":
                return d.argumentation;
            case "constructiveness":
                return d.constructiveness;
            case "sarcasm":
                return d.sarcasm;
            case "mockery":
                return d.mockery;
            case "intolerance":
                return d.intolerance;
            case "improper_language":
                return d.improper_language;
            case "insult":
                return d.insult;
            case "aggressiveness":
                return d.aggressiveness;
            case "gray":
                return 1;
            case "gray-ring":
                return 0.5;

            //Targets
            case "target-group":
                return d.target_group;
            case "target-person":
                return d.target_person;
            case "target-stereotype":
                return d.stereotype;

            //Toxicity
            case "toxicity-0":
                return d.toxicity_level === 0 ? 1 : 0;
            case "toxicity-1":
                return d.toxicity_level === 1 ? 1 : 0;
            case "toxicity-2":
                return d.toxicity_level === 2 ? 1 : 0;
            case "toxicity-3":
                return d.toxicity_level === 3 ? 1 : 0;

            //Stances
            case "positive":
                return d.positive_stance;
            case "negative":
                return d.negative_stance;
            case "neutral":
                return !(d.positive_stance || d.negative_stance);
            case "both":
                return d.positive_stance && d.negative_stance;

            default:
                //console.log("An attribute could not be retrieved because the key word did not match any case...");
                return 1;
        }
    }

    function highlightNode(node, attributeName) {
        node.filter(function (d) {
            return retrieveAttributeFromComment(d.data, attributeName);
        }).style("stroke", "black").style("color", "black").style("opacity", maxOpacityValue);
    }

    function unhighlightNode(node, attributeName) {
        node.filter(function (d) {
            return !retrieveAttributeFromComment(d.data, attributeName);
        }).style("stroke", "black").style("color", "black").style("opacity", minOpacityValue);
    }

    /**
     * Highlight a node if the checkbox is checked and if the node presents a certain level of toxicity
     * */
    function highlightByToxicity(node, enabledHighlight, changeNodeOpacity) {
        if (enabledHighlight.indexOf("highlight-toxicity-0") > -1) changeNodeOpacity(node, "toxicity-0");
        if (enabledHighlight.indexOf("highlight-toxicity-1") > -1) changeNodeOpacity(node, "toxicity-1");
        if (enabledHighlight.indexOf("highlight-toxicity-2") > -1) changeNodeOpacity(node, "toxicity-2");
        if (enabledHighlight.indexOf("highlight-toxicity-3") > -1) changeNodeOpacity(node, "toxicity-3");
    }

    function highlightByStance(node, enabledHighlight, changeNodeOpacity) {
        if (enabledHighlight.indexOf("highlight-stance-neutral") > -1) changeNodeOpacity(node, "neutral");
        if (enabledHighlight.indexOf("highlight-stance-positive") > -1) changeNodeOpacity(node, "positive");
        if (enabledHighlight.indexOf("highlight-stance-negative") > -1) changeNodeOpacity(node, "negative");
        if (enabledHighlight.indexOf("highlight-both") > -1) changeNodeOpacity(node, "both");
    }

    function highlightByTarget(node, enabledHighlight, changeNodeOpacity) {
        if (enabledHighlight.indexOf("highlight-target-group") > -1) changeNodeOpacity(node, "target-group");
        if (enabledHighlight.indexOf("highlight-target-person") > -1) changeNodeOpacity(node, "target-person");
        if (enabledHighlight.indexOf("highlight-target-stereotype") > -1) changeNodeOpacity(node, "target-stereotype");
    }

    /**
     * Highlight a node if the checkbox is checked and if the node presents the feature
     * */
    function highlightByFeature(node, enabledHighlight, changeNodeOpacity) {
        if (enabledHighlight.indexOf("highlight-features-argumentation") > -1) changeNodeOpacity(node, "argumentation");
        if (enabledHighlight.indexOf("highlight-features-constructiveness") > -1) changeNodeOpacity(node, "constructiveness");

        if (enabledHighlight.indexOf("highlight-features-sarcasm") > -1) changeNodeOpacity(node, "sarcasm");
        if (enabledHighlight.indexOf("highlight-features-mockery") > -1) changeNodeOpacity(node, "mockery");
        if (enabledHighlight.indexOf("highlight-features-intolerance") > -1) changeNodeOpacity(node, "intolerance");

        if (enabledHighlight.indexOf("highlight-features-improper-language") > -1) changeNodeOpacity(node, "improper_language");
        if (enabledHighlight.indexOf("highlight-features-insult") > -1) changeNodeOpacity(node, "insult");
        if (enabledHighlight.indexOf("highlight-features-aggressiveness") > -1) changeNodeOpacity(node, "aggressiveness");
    }

    // Div where the title of the "Static Values" is displayed
    var statisticBackground = d3.select("#circletree-container")
        .append("div")
        .attr("class", "my-statistic") //add the tooltip class
        .style("position", "absolute")
        .style("z-index", "1") //it has no change
        .style("visibility", "visible")
        .style("right", "320px");

    // Div where the zoom buttons are displayed
    var zoomBackground = d3.select("body")
        .append("div")
        .style("position", "absolute")
        .style("z-index", "0") //it has no change
        .style("visibility", "visible");

    // Div where the sum up information of "Static Values" is displayed
    var statisticTitleBackground = d3.select("#circletree-container")
        .append("div")
        .attr("class", "my-statistic-title") //add the tooltip class
        .style("position", "absolute")
        .style("z-index", "0") //it has no change
        .style("visibility", "visible");

    /*SECTION zoom - TODO*/
});


