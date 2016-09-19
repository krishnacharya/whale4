


function randomized(data){
    var treeData = data.list;
    var round=data.round;

    var margin = {top: 20, right: 60, bottom: 20, left: 60},
        width = $("#graph").width() - margin.right - margin.left,
        height = window.innerHeight/1.4- margin.top - margin.bottom;

    var colorRange = d3.scale.category20();

    var i = 0;

    var tree = d3.layout.tree()
        .size([height, width]);



    d3.select("svg").remove();
    d3.select("div#control").remove();


    d3.select("#graph").append("div").attr("id","control")
        .append("input")
        .attr("type","button")
        .attr("class","btn btn-success")
        .attr("id"," Shuffle_randomized")
        .attr("value","Shuffle candidates for the first round")
        .on("click",graph);



    var svg = d3.select("#graph").append("svg")
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    root = treeData[0];

    update(root);

    function update(source) {

        // Compute the new tree layout.
        var nodes = tree.nodes(root).reverse(),
            links = tree.links(nodes);

        // Normalize for fixed-depth.
        nodes.forEach(function (d) {
            d.y = width-d.depth*width/round;
        });

        // Declare the nodesâ€¦
        var node = svg.selectAll("g.node")
            .data(nodes, function (d) {
                return d.id || (d.id = ++i);
            });

        // Enter the nodes.
        var nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", function (d) {
                return "translate(" +  (d.y) + "," +  (d.x) + ")";
            });



        nodeEnter.append("circle")
            .attr("r", 10)
            .style("fill", function (d) {return colorRange(d.name);})
            .style("stroke", function (d) {return colorRange(d.name);});

        nodeEnter.append("text")
            .attr("x", 0)
            .attr("y",-20)
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .text(function (d) {return d.name;})
            .style("fill", function (d) {return colorRange(d.name);});

        nodeEnter.append("text")
            .attr("x", width/(round*2)-10)
            .attr("y",-10)
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .text(function (d) {return d.diff;})
            .style("fill", function (d) {return colorRange(d.name);});


        var link = svg.selectAll("path.link")
            .data(links, function (d) {
                return d.target.id;
            });


        link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("d", elbow);

        function elbow(d, i) {
            return "M" + d.target.y + "," + d.target.x
                + "H" + (d.source.y-width/(round*2)) + "V" + d.source.x + "H" + d.source.y
                + (d.source.children ? "" : "h" + margin.right);
        }
    }

}