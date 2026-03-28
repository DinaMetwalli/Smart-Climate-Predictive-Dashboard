/**
 * Requests the prediction results from the session through
 * an API call and passes the results to create the chart.
 */
async function loadPredsChart() {
    try {
        console.log("Loading Predictions Chart...");
        const response = await fetch(`/api/charts/preds`);
        const predictions = await response.json();

        // Return if no analysis request has been processed and no stats have been set yet
        if (predictions == null) {
            return;
        }

        displayPredsChart(predictions);
    } catch (error) {
        console.error('Error loading predictions:', error);
    }
}

/**
 * Creates the chart and updates the HTML.
 * @param  {Object} predictions - the prediction results to be displayed in the line chart.
 */
function displayPredsChart(predictions) {
    const continents = Object.keys(predictions);
    
    const lineColors = [
        '#4ba5c9',
        '#8957e1',
        '#32d7ae',
        '#ffa45e',
        '#41d2ec',
        '#ff6b6e'
    ];

    const data = continents.map((continent, index) => {
        const values = predictions[continent];
        return {
            x: Array.from({ length: values.length }, (_, i) => i),
            y: values,
            name: continent.charAt(0).toUpperCase() + continent.slice(1),
            type: 'scatter',
            mode: 'lines',
            line: {
                color: lineColors[index % lineColors.length],
                width: 3
            },
            hovertemplate: `<b>${continent.toUpperCase()}</b><br>Step: %{x}<br>Value: %{y:.4f}<extra></extra>`
        };
    });

    const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: '#181c22',
        hoverlabel: {
            bgcolor: '#161B22',
            bordercolor: '#30363D',
            font: {
                family: 'Comfortaa, sans-serif',
                size: 12,
                color: '#F0F6FC'
            }
        },
        font: {
            family: 'Comfortaa, sans-serif',
            color: '#F0F6FC'
        },
        margin: { t: 40, r: 40, l: 60, b: 60 },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2,
            x: 0.5,
            xanchor: 'center'
        },
        xaxis: {
            title: 'Prediction Step',
            gridcolor: '#30363D',
            linecolor: '#30363D'
        },
        yaxis: {
            title: 'Predicted Value',
            gridcolor: '#30363D',
            linecolor: '#30363D',
            zerolinecolor: '#8B949E'
        }
    };

    const config = {
        responsive: true,
        displayModeBar: true
    };

    Plotly.newPlot('preds-chart', data, layout, config);
}

// An event listener to check for page loading.
document.addEventListener('DOMContentLoaded', loadPredsChart);