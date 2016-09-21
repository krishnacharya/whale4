

var url=d3.select("#url_poll").property("value");
var method=d3.select("#method").property("value");
var preference=d3.select("#preference").property("value");
    d3.select("#controlApproval").style("visibility","hidden");
d3.select("#controlCondorcet").style("visibility","hidden");
d3.select("#Shuffle_randomized").style("visibility","hidden");


function graph() {

    d3.json(url, function(error, data) {

        method= parseInt(method);

        switch(method) {
            case 1:
                if(preference == "Approval") {
                d3.select("#control").style("visibility","hidden");
                    }
                scoring_plot(data.scoring);
                break;
            case 2:
                condorcet_plot(data.condorcet);
                break;

            case 3:
                runoff_plot(data.runoff);
                break;
            case 4:
                randomized(data.randomized);

        }
    });
}



graph();

d3.select("#option").on("change", graph);

d3.select("#approval").on("change", graph);
d3.select("#graph_type").on("change", graph);

d3.select(window).on('resize', graph);

function wrap(text, width) {
    text.each(function() {
        var text = d3.select(this),
            words = text.text().split("#").reverse(),
            word,
            line = [],
            lineNumber = 0,
            lineHeight = 1.1, // ems
            y = text.attr("y"),
            dy = parseFloat(text.attr("dy")),
            tspan = text.text(null).append("tspan").attr("x", 0).attr("y", y).attr("dy", dy + "em");
        while (word = words.pop()) {
            line.push(word);
            tspan.text(line.join(" "));
            if (tspan.node().getComputedTextLength() > width) {
                line.pop();
                tspan.text(line.join(" "));
                line = [word];
                tspan = text.append("tspan").attr("x", 0).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
            }
        }
    });
}


