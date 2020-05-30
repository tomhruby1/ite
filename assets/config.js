//colors
const green = 'rgb(64, 165, 64)';
const red = 'rgb(229,43,80)';
const blue = 'rgb(25, 118, 210)';
const black = 'rgb(33, 33, 33)';
const pink = 'rgb(255, 64, 129)';
const yellow= 'rgb(253, 216, 53)';
const orange= 'rgb(239, 108, 0)';
//transparent variants of colors
const greenT = 'rgba(64, 165, 64,0.3)';
const redT = 'rgba(229,43,80,0.3)';
const blueT = 'rgba(25, 118, 210, 0.3)';
const blackT = 'rgba(33, 33, 33, 0.3)';
const pinkT = 'rgba(255, 64, 129, 0.3)';
const yellowT= 'rgba(253, 216, 53, 0.3)';
const orangeT= 'rgba(239, 108, 0, 0.3)';

/*Get rgb color from given team id*/
function getColor(id, transparent = false){
    if(transparent){
        colors = [greenT, blackT, pinkT, yellowT, blueT, orangeT,redT];
        return colors[id-1];
    }else{
        colors = [green, black, pink, yellow, blue, orange,red];
        return colors[id-1];
    }
}

function getGraphConfig(id, data, times){
  color = getColor(id);
  config = {
      // The type of chart we want to create
      type: 'line',

      // The data for our dataset
      data: {
          labels: times,
          datasets: [{
              //label: id.toString(),
              backgroundColor: color,
              borderColor: color,
              data: data
          },
      ]
      },

      // Configuration options go here
      options: {
        legend:{
          display: false
        },
        scales: {
            yAxes: [{
                ticks: {
                    suggestedMin: 15,
                    suggestedMax: 30,
                    callback: function(value, index, values) {
                        return value + ' C°'
                    }
                }
            }]
        }
      }
  }

  return config
}

function getHistGraphConfig(datasets, time){
  config = {
  // The type of chart we want to create
  type: 'line',

  // The data for our dataset
  data: {
      labels: time,
      datasets,
  },

  // Configuration options go here
  options: {
    scales:{
      yAxes:[{
        ticks:{
          callback: function(value, index, values){
            return value + ' C°'
          }
       }
     }]
    }
  }
}

return config
}
