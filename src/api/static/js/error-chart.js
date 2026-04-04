/**
 * Requests the error accumulation values from the session through
 * an API call and passes the results to create the chart.
 */
async function loadErrorsChart() {
    try {
        console.log("Loading Errors Chart...");
        const response = await fetch(`/api/charts/errors`);
        const errors = await response.json();

        // Return if no analysis request has been processed and no stats have been set yet
        if (errors == null) {
            return;
        }

        displayHorizonChart(errors);
    } catch (error) {
        console.error('Error loading errors:', error);
    }
}

/**
 * Creates the heatmap and updates the HTML.
 * @param  {Object} errorData - the error accumulation values per-continent.
 */
function displayHorizonChart(errorData) {
    const regions = Object.keys(errorData);
    const zValues = regions.map(r => errorData[r]);

    const data = [{
        z: zValues,
        x: Array.from({length: 60}, (_, i) => i + 1),
        y: regions.map(r => r.toUpperCase()),
        type: 'heatmap',
        colorscale: 'Viridis',
        hoverongaps: false,
        hovertemplate: 'Region: %{y}<br>Month: %{x}<br>Error: %{z:.4f}°C<extra></extra>'
    }];

    const layout = {
        title: 'Error Intensity Over Forecast Horizon',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: '#181c22',
        font: { family: 'Comfortaa', color: '#F0F6FC' },
        xaxis: { title: 'Months Ahead', gridcolor: '#30363D' },
        yaxis: { autorange: 'reversed' },
        margin: { l: 120, r: 20, t: 50, b: 50 }
    };

    Plotly.newPlot('errors-chart', data, layout);
}

// An event listener to check for page loading.
document.addEventListener('DOMContentLoaded', loadErrorsChart);