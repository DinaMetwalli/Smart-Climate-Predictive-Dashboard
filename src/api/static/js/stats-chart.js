/**
 * Requests the performance metrics values from the session through
 * an API call and passes the results to create the chart.
 */
async function loadStatsCharts() {
    try {
        console.log(`Loading Summary Statistics & Radar Charts...`);
        const response = await fetch(`/api/charts/stats`);
        const stats = await response.json();

        // Return if no analysis request has been processed and no stats have been set yet
        if (stats == null) {
            return;
        }

        displayStatsChart(stats);
        displayRadarChart(stats);
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

/**
 * Creates the bar chart and updates the HTML.
 * @param  {Object} stats - the RMSE, Mean Bias, and Correlation values.
 */
function displayStatsChart(stats) {
    const continents = Object.keys(stats);
    const metrics = ['rmse', 'mean_bias', 'correlation'];
    
    const colorMap = {
        'rmse': '#4ba5c9',
        'mean_bias': '#8957e1',
        'correlation': '#32d7ae'
    };

    const data = metrics.map(metric => ({
        x: continents.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
        y: continents.map(c => stats[c][metric]),
        name: metric.replace('_', ' ').toUpperCase(),
        type: 'bar',
        marker: { color: colorMap[metric] || '#ffffff', line: { color: '#181c22', width: 1 }}
    }));

    const layout = {
        title: 'Per-continent backtest metrics (RMSE, Mean Bias, Correlation)',
        barmode: 'group',
        bargap: 0.3,
        hovermode: 'closest',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: '#181c22',
        font: {
            family: 'Comfortaa, sans-serif',
            color: '#F0F6FC'
        },
        showlegend: true,
        legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
        xaxis: {
            gridcolor: '#30363D',
            linecolor: '#30363D',
            zeroline: false,
            tickfont: {size: 14}
        },
        yaxis: {
            gridcolor: '#30363D',
            linecolor: '#30363D',
            zerolinecolor: '#8B949E',
            nticks: 15,
            showgrid: true,
            gridcolor: '#30363D',
            gridwidth: 1,
            showticklabels: true,
            tickfont: {size: 14, color: '#8B949E'}
        }
    };

    const config = {
        responsive: true,
        displayModeBar: true
    };

    Plotly.newPlot('stats-chart', data, layout, config);
}

/**
 * Creates the radar chart and updates the HTML.
 * @param  {Object} stats - the RMSE, Mean Bias, and Correlation values.
 */
function displayRadarChart(stats) {
    const regions = Object.keys(stats);
    const rmseValues = regions.map(r => stats[r].rmse);
    const closedRegions = [...regions.map(r => r.toUpperCase()), regions[0].toUpperCase()];
    const closedRMSE = [...rmseValues, rmseValues[0]];

    const data = [{
        type: 'scatterpolar',
        r: closedRMSE,
        theta: closedRegions,
        fill: 'toself',
        name: 'Model RMSE',
        line: { color: '#32d7ae' },
        fillcolor: 'rgba(50, 215, 174, 0.3)',
        hovertemplate: 'Region: %{theta}<br>Avg RMSE: %{r:.4f}<extra></extra>'
    }];

    const layout = {
        title: 'Regional Accuracy Balance (Backtest RMSE)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        polar: {
            bgcolor: '#1c2128',
            radialaxis: {
                visible: true,
                range: [0, Math.max(...rmseValues) * 1.2],
                color: '#8B949E',
                gridcolor: '#30363D'
            },
            angularaxis: {
                color: '#F0F6FC',
                gridcolor: '#30363D',
                linecolor: '#30363D'
            }
        },
        margin: { t: 40, r: 10, l: 10, b: 40 },
        font: { family: 'Comfortaa', color: '#F0F6FC' },
        showlegend: false
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('radar-chart', data, layout, config);
}

// An event listener to check for page loading.
document.addEventListener('DOMContentLoaded', loadStatsCharts);