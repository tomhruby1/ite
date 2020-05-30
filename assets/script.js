const wsUrl = "ws://147.228.121.46:8882";

const id2col = ["0","green", "black", "pink", "yellow", "blue", "orange", "red"];

//Websockets Connection after body loaded
function onBodyLoad(){
       if ("WebSocket" in window) {
        console.log("WebSocket is supported by your browser.");

        var ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log("Connection is opened ...");
        };
        ws.onmessage = function (evt) {
            var msg = evt.data;
            console.log("Message is received: " + msg);
            displayValues(msg)
        };

        ws.onclose = function() {
            console.log("Connection is closed ...");
        };

    } else {
        console.log("WebSocket not supported by your browser.");
    }
}

//data from tornado
function setHistData(vals){
      console.log("HISTORIJE:");
      console.log(vals);
      drawHistGraph(vals)
}

//draw past 24hrs history to one graph
function drawHistGraph(valsDict){
    var ctx = document.getElementById("chart0").getContext('2d');
    var datasets = [];

    for (i = 1; i < 8; i++) {
        var dataset = new Object;
        dataset.label = id2col[i];
        dataset.borderColor = getColor(i, false);
        dataset.backgroundColor = getColor(i, true);
        dataset.data = valsDict[i].data;

        if(i > 1) //other than first team defaultly hidden
          dataset.hidden = true

        datasets[i-1] = dataset;
    }
        var chart = new Chart(ctx, getHistGraphConfig(datasets, valsDict[1].time)); //graphConfigs in config.js, time axis using from first team
}

/*Display RealTime data*/
function displayValues(vals){
    var valsDict = JSON.parse(vals);
    id = valsDict["id"];
    data =  valsDict["data"];
    currentVal = data[data.length-1]; //last last value in data array is current value
    times = valsDict["times"];

    maxVal = valsDict["max"];
    minVal = valsDict["min"];
    avgVal = valsDict["avg"];

    stat = valsDict["status"];

    if(stat == "online" || stat == "alert")
      document.getElementById("val".concat(id)).innerHTML = `<li> ${currentVal} <c class="degSign">°C</c> </li>`; //display live value
    else {
      document.getElementById("val".concat(id)).innerHTML = " ";
    }

    document.getElementById("max".concat(id)).innerHTML = `${maxVal} <c class="degSign">°C</c>`; //display max value
    document.getElementById("min".concat(id)).innerHTML = `${minVal} <c class="degSign">°C</c>`; //display min value
    document.getElementById("avg".concat(id)).innerHTML = `${avgVal} <c class="degSign">°C</c>`; //display avg value

    if(stat == "online"){ //set status color
        colorChange("stat".concat(id), green);
    }else if(stat == "offline"){
        colorChange("stat".concat(id), red);
    }else {
        colorChange("stat".concat(id), yellow);
    }

    document.getElementById("stat".concat(id)).innerHTML = stat; //display status

    drawGraph(id,data,times);
}

//changes color of html element given id
function colorChange(id, color){
    document.getElementById(id).style.color = color;
}

//draw RealTime chart
function drawGraph(id, data, times){
        var ctx = document.getElementById("chart".concat(id)).getContext('2d');
        var chart = new Chart(ctx, getGraphConfig(id, data, times)); // graphConfigs in config.js
}
