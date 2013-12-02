var viewer;

$(document).ready(function(){          
  start();
  $("#grafos").change(onSelectChange);            
  $("#txtSearch").autocomplete({                  
    source : function(request, response){
      data = search($("#txtSearch").val());
      response(data); 
    },
    minLength : 3,
    select : function(event, ui){
      highlight(ui.item.label);
    }
  }).keypress(function(e){
    var code = (e.keycode ? e.keycode : e.which);
    if (code == 13) {
      return false;
    }
  });                  
});
            
function onSelectChange(){
  $("#imgLoading").css({ display: "inline" });
  var selected = $("#grafos option:selected");
  var thereIsImage = false;
  var heigthImage = 0;
  var desLength = 0;
  var metricsLength = 0;

  var data = {
  "date": "Mon Dec 02 10:20:25 CET 2013",
  "author": "jorgaf",
  "description": "File created by Web site exporter. http://loxa.ec",
  "graphs": [
    {
      "name": "Workspace0",
      "title": "Title to Workspace0",
      "tip": "",
      "nodes": "2141",
      "edges": "42422",
      "description": "",
      "imgColorDescription": "Workspace0/imgDescriptor.png",
      "graphfile": "Workspace0/Workspace0.csv",
      "pdffile": "Workspace0/Workspace0.pdf",
      "browsegraph": "{{ url_for('static', filename='geodataviz.gexf') }}",
      "type": "Directed",
      "metrics": [
        {
          "name": "Metric 1",
          "value": "0,00",
          "description": "Description for metric 1"
        },
        {
          "name": "Metric 2",
          "value": "0,00",
          "description": "Description for metric 2"
        },
        {
          "name": "Metric 3",
          "value": "0,00",
          "description": "Description for metric 3"
        },
        {
          "name": "Metric 4",
          "value": "0,00",
          "description": "Description for metric 4"
        },
        {
          "name": "Metric 5",
          "value": "0,00",
          "description": "Description for metric 5"
        },
        {
          "name": "Metric 6",
          "value": "0,00",
          "description": "Description for metric 6"
        },
        {
          "name": "Metric 7",
          "value": "0,00",
          "description": "Description for metric 7"
        },
        {
          "name": "Metric 8",
          "value": "0,00",
          "description": "Description for metric 8"
        }
      ]
    }
  ]
}

    $.each(data.graphs, function(i, item){    
        
      if(selected.val() == item.name){                  
        $("#txtSearch").val("");
        //sigma
        $('#sigma-example').empty();
        paintViewer(item.browsegraph)
        
        $("#tituloGrafico").html(item.title);
        $("#tituloData").html(item.title);
        
        if(item.tip != ""){
          $("#hallazgos").html(item.tip);
        } else {
          $("#hallazgos").html("&nbsp;");
        }
                
        $("#nodesValue").html(item.nodes);
        $("#edgesValue").html(item.edges);
        $("#typeValue").html(item.type);

        $("#descriptionValue").html(item.description);
        desLength = item.description.length;          
        
        if(item.imgColorDescription != ""){                   
          $("#descriptionValue").append("<br/><img id='imgDescription' src='" + item.imgColorDescription + "' />");   
          thereIsImage = true;       

          $("#imgDescription").load(function(){
            heigthImage = $("#imgDescription").height();
            configGeneralInfo(desLength, thereIsImage, heigthImage, metricsLength);            
          });          
        }

        metricsLength = item.metrics.length;
        if(item.metrics.length > 0){
          $("#lblMetrics").css({ display: "inline" });
          var output = "<table class='table table-condensed'>";          
          for(i = 0; i < item.metrics.length; i ++){                      
            output += "<tr><td><span class='text-info' rel='popover' data-trigger='click' data-placement='bottom' data-html='true' data-original-title='Metric description' data-content='"   
               + item.metrics[i].description 
               + "'>" 
               + item.metrics[i].name 
               + "</span></td>" 
               + "<td style='text-align:right'>" + item.metrics[i].value + "</td>"
               +"</tr>";            
          }          
          output += "</table>"; 
          output += "<script type='text/javascript'> $('[rel=\"popover\"]').popover();</script>";         
          $("#metricsTable").html(output);          
        } else{
          $("#lblMetrics").css({ display: "none" });
          $("#metricsTable").html("");
        }       

        $("#descargar").attr("href", item.pdffile);
        $("#downloadCSV").attr("href", item.graphfile);   

        configGeneralInfo(desLength, thereIsImage, heigthImage, metricsLength);     
      }
      $("#imgLoading").css({ display: "none" });
    });


/*  $.getJSON('/static/estadisticas.json',
  
  function(data){   
    $.each(data.graphs, function(i, item){    
        
      if(selected.val() == item.name){                  
        $("#txtSearch").val("");
        //sigma
        $('#sigma-example').empty();
        paintViewer(item.browsegraph)
        
        $("#tituloGrafico").html(item.title);
        $("#tituloData").html(item.title);
        
        if(item.tip != ""){
          $("#hallazgos").html(item.tip);
        } else {
          $("#hallazgos").html("&nbsp;");
        }
                
        $("#nodesValue").html(item.nodes);
        $("#edgesValue").html(item.edges);
        $("#typeValue").html(item.type);

        $("#descriptionValue").html(item.description);
        desLength = item.description.length;          
        
        if(item.imgColorDescription != ""){                   
          $("#descriptionValue").append("<br/><img id='imgDescription' src='" + item.imgColorDescription + "' />");   
          thereIsImage = true;       

          $("#imgDescription").load(function(){
            heigthImage = $("#imgDescription").height();
            configGeneralInfo(desLength, thereIsImage, heigthImage, metricsLength);            
          });          
        }

        metricsLength = item.metrics.length;
        if(item.metrics.length > 0){
          $("#lblMetrics").css({ display: "inline" });
          var output = "<table class='table table-condensed'>";          
          for(i = 0; i < item.metrics.length; i ++){                      
            output += "<tr><td><span class='text-info' rel='popover' data-trigger='click' data-placement='bottom' data-html='true' data-original-title='Metric description' data-content='"   
               + item.metrics[i].description 
               + "'>" 
               + item.metrics[i].name 
               + "</span></td>" 
               + "<td style='text-align:right'>" + item.metrics[i].value + "</td>"
               +"</tr>";            
          }          
          output += "</table>"; 
          output += "<script type='text/javascript'> $('[rel=\"popover\"]').popover();</script>";         
          $("#metricsTable").html(output);          
        } else{
          $("#lblMetrics").css({ display: "none" });
          $("#metricsTable").html("");
        }       

        $("#descargar").attr("href", item.pdffile);
        $("#downloadCSV").attr("href", item.graphfile);   

        configGeneralInfo(desLength, thereIsImage, heigthImage, metricsLength);     
      }
      $("#imgLoading").css({ display: "none" });
    });
  });*/
}
function configGeneralInfo(dLength, existsImage, hImage, metricsSize){
  var totalSize = dLength + hImage + (metricsSize * 29);
  if(totalSize >= 1000){
    $("#generalInfo").height('600px');    
    $("#generalInfo").css('overflow', 'scroll');
  } else {
    $("#generalInfo").height('auto');
    $("#generalInfo").css('overflow', 'auto');
  }
  /*alert(dLength + " " + hImage + " " + existsImage);
  alert(totalSize + " " + existsImage);*/

}
function paintViewer(gexfPath){
  viewer = sigma.init(document.getElementById('sigma-example')).drawingProperties({
    defaultLabelColor: '#fff',
    defaultLabelSize: 14,
    defaultLabelBGColor: '#fff',
    defaultLabelHoverColor: '#000',
    labelThreshold: 1,
    defaultEdgeType: 'curve'
  }).graphProperties({
    minNodeSize: 0.5,
    maxNodeSize: 1.5,
    minEdgeSize: 1,
    maxEdgeSize: 1
  }).mouseProperties({
    maxRatio: 40
  });
  viewer.parseGexf(gexfPath);
  var greyColor = '#666';
  viewer.bind('overnodes',function(event){
    var nodes = event.content;
    var neighbors = {};
    viewer.iterEdges(function(e){
      if(nodes.indexOf(e.source)<0 && nodes.indexOf(e.target)<0){
        if(!e.attr['grey']){
          e.attr['true_color'] = e.color;
          e.color = greyColor;
          e.attr['grey'] = 1;
        }
      }else{
        e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
        e.attr['grey'] = 0;
 
        neighbors[e.source] = 1;
        neighbors[e.target] = 1;
      }
    }).iterNodes(function(n){
      if(!neighbors[n.id]){
        if(!n.attr['grey']){
          n.attr['true_color'] = n.color;
          n.color = greyColor;
          n.attr['grey'] = 1;
        }
      }else{
        n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
        n.attr['grey'] = 0;
      }
    }).draw(2,2,2);
  }).bind('outnodes',function(){
    viewer.iterEdges(function(e){
      e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
      e.attr['grey'] = 0;
    }).iterNodes(function(n){
      n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
      n.attr['grey'] = 0;
    }).draw(2,2,2);
  });
  
  viewer.draw();  
}
            
function start() {  
  onSelectChange();
}

function configView(valor){
  $('#grafos').val(valor).attr('selected', 'selected');
  onSelectChange();
}

//Based on http://gnutiez.de/wp/2012/12/19/animated-node-highlighting-with-sigma-js
function search(nodeName) {   
  var output =  new Array();
  //Loop all nodes
  viewer.iterNodes(function(n) {
    //if node label or index contains sarchterm
    if((n.label.toLowerCase().substring(0, nodeName.length) === nodeName.toLowerCase()) && nodeName != "") {           
      output.push(n.label);      
    }    
  }); 
  return output;
}

//Based on http://gnutiez.de/wp/2012/12/19/animated-node-highlighting-with-sigma-js
function highlight(nodeName) {
  var data =  new Array();
  if(nodeName != "") {  
    //Center Graph
    viewer.position(0,0,1).draw(2,2,2);
  }  
  //Loop all nodes
  viewer.iterNodes(function(n) {
    //creating new node attribute "big" to indicate if it is highlighted
    n.attr["big"] = 0;
    //if node label or index contains sarchterm
    if((n.label.toLowerCase() === nodeName.toLowerCase()) && nodeName != "") {             
      viewer.zoomTo(n['displayX'],n['displayY'],40);
    }
  }).draw(2, 2, 2)
}
