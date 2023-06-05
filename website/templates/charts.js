



function run_stock(){
for(var i = 0; i < 4; i++) {
// console.log(plotDataJson[i]['stock name']); 
new ChartworksBuilder({

"token": "demo-token",
"target": "#chartTarget",
"symbol": stocks_names[i],
"exchange": "NSQ",
"timeframe": "1y",
"realTime": false,
"typeAheadAPI": "https://api.markitondemand.com/apiman-gateway/MOD/chartworks-xref/1.0/xref/predictive?search=%s",
"compareMenuOptions": [{
"symbol": "INFO",
"exchange": "NYSE",
"displayName": "IHS Markit Ltd."
}],
"cultureCode": "en-US",
"style.indicator.price.lineColor": "orange",
"style.indicator.price.fillColor": "rgba(95, 179, 241, 0.1)",
"style.indicator.price.lineWidth": "3",
"panel.lower.indicator": "Volume",
"feature.symbolSearch": true,
"feature.comparison": true,
"feature.timeframe": true,
"feature.indicators": true,
"feature.intraday": true,
"feature.events": true,
"feature.markerType": true,
"feature.saveLoad": true,
"feature.share": true,
"feature.tools": true,
"theme": "dark",
"onShare": function(args) {
var sharePenURL = "https://codepen.io/chartworks/pen/ZpgQEb?chartID=" + args.chartID;

// Display Dialog with link to our chart
this.showDialog("<a href=" + sharePenURL + " target=\"_blank\">View Your Shared Chart in CodePen</a>");
},
"onPrimarySymbolChange": function(args) {
console.log(args.symbol, args.exchangeId);

// Display a nice message when trying to get unentitled data
if (args.symbol != "AAPL" && args.symbol != "INFO") {
this.showDialog("Alert", "This demo is only entitled to symbols AAPL on the NASDAQ and INFO on the NYSE. All other symbols will fail.");
}
},
"onAPIError": function(apiError) {
// handle 401 (unauthorized)
if (apiError.status === 401) {
// show dialog that we are getting a new token
this.showDialog("Token expired", "Loading new token...");

// use getInvalidTokenCount to ensure we don't get stuck in an
// endless loop if we keep creating bad tokens
if (this.getInvalidTokenCount() < 5) {
var objChart = this;
getNewToken(function(newToken) {
// set token
objChart.setConfigParam("token", newToken);

// load data
objChart.loadData();
});
} else { // fail after 5 unsuccessful tries
this.showDialog("Warning", "Max number of auth attempts reached. Your token generation is no good!");
}
} else { // print other errors in the console
console.log(apiError.status, apiError.statusMsg);
}
}
});

// Your code should generate a new token.
// This is just an example
function getNewToken(onComplete) {
// timeout to simulate a slow request
setTimeout(function() {
var token = "demo-token";
onComplete(token);
}, 1000);
}}}