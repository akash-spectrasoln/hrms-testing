function getChartColorsArray(e){if(null!==document.getElementById(e))return e=document.getElementById(e).getAttribute("data-colors"),(e=JSON.parse(e)).map(function(e){var t=e.replace(" ","");return-1===t.indexOf(",")?getComputedStyle(document.documentElement).getPropertyValue(t)||t:2==(e=e.split(",")).length?"rgba("+getComputedStyle(document.documentElement).getPropertyValue(e[0])+","+e[1]+")":t})}function ChartColorChange(t,o){document.querySelectorAll(".theme-color").forEach(function(e){e.addEventListener("click",function(e){setTimeout(()=>{var e=getChartColorsArray(o);t.updateOptions({colors:e})},0)})})}