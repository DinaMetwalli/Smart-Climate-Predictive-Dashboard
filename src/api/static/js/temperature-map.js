async function loadPredictions(monthIndex, sliderDate) {
    try {
        console.log(`Fetching month ${monthIndex}...`);

        const response = await fetch(`/analysis/predictions/${monthIndex}`);
        const data = await response.json();

        if (sliderDate) sliderDate.textContent = `Month: ${data.date}`;

        displayMap(data.continents);
    } catch (error) {
        console.error('error:', error);
    }
}

function displayMap(continents) {
    // Prepare data for Plotly
    const locations = [];
    const values = [];
    
    // Map ISO-3 codes to continents
    const continentMapping = {
        "Africa": [
            "DZA","AGO","BEN","BWA","BFA","BDI","CPV","CMR","CAF","TCD","COM","COD","COG",
            "DJI","EGY","GNQ","ERI","SWZ","ETH","GAB","GMB","GHA","GIN","GNB","CIV","KEN",
            "LSO","LBR","LBY","MDG","MWI","MLI","MRT","MUS","MAR","MOZ","NAM","NER","NGA",
            "RWA","STP","SEN","SYC","SLE","SOM","ZAF","SSD","SDN","TZA","TGO","TUN","UGA",
            "ZMB","ZWE","ESH"
        ],
        "Asia": [
            "AFG","ARM","AZE","BHR","BGD","BTN","BRN","KHM","CHN","CYP","GEO","IND","IDN",
            "IRN","IRQ","PSE","JPN","JOR","KAZ","KWT","KGZ","LAO","LBN","MYS","MDV","MNG",
            "MMR","NPL","PRK","OMN","PAK","PHL","QAT","RUS","SAU","SGP","KOR","LKA","SYR",
            "TWN","TJK","THA","TLS","TUR","TKM","ARE","UZB","VNM","YEM"
        ],
        "Europe": [
            "ALB","AND","AUT","BLR","BEL","BIH","BGR","HRV","CZE","DNK","EST","FIN","FRA",
            "DEU","GRC","HUN","ISL","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MLT","MDA",
            "MCO","MNE","NLD","MKD","NOR","POL","PRT","ROU","SMR","SRB","SVK","SVN","ESP",
            "SWE","CHE","UKR","GBR","VAT"
        ],
        "North America": [
            "ATG","BHS","BRB","BLZ","CAN","CRI","CUB","DMA","DOM","SLV","GRD","GTM","HTI",
            "HND","JAM","MEX","NIC","PAN","KNA","LCA","VCT","TTO","USA","GRL"
        ],
        "South America": [
            "ARG","BOL","BRA","CHL","COL","ECU","GUY","PRY","PER","SUR","URY","VEN","GUF"
        ],
        "Oceania": [
            "AUS","FJI","KIR","MHL","FSM","NRU","NZL","PLW","PNG","WSM","SLB","TON","TUV","VUT"
        ],
        "Antarctica": ["ATA"]
    };

    // Mapping of continent centers based on latitudes and longitudes for label positions
    const continentCenters = {
        "Africa": {lat: 2, lon: 22},
        "Asia": {lat: 45, lon: 90},
        "Europe": {lat: 54, lon: 20},
        "North America": {lat: 45, lon: -100},
        "South America": {lat: -15, lon: -60},
        "Oceania": {lat: -25, lon: 135}
    };
    
    // Assign the continent values to each of their countries
    Object.entries(continents).forEach(([name, value]) => {
        const countries = continentMapping[name];

        if (!countries) return;

        countries.forEach(country => {
            locations.push(country);
            values.push(value);
        });
    });
    
    // Create the plotly map data
    const mapData = [{
        type: 'choropleth',
        locationmode: 'ISO-3',
        locations: locations,
        z: values,
        hoverinfo: 'skip',
        zmin: -3,
        zmax: 5,
        colorscale: [
            [0,    '#e8d5f5'],
            [0.25, '#a78de8'],
            [0.5,  '#6c63d4'],
            [0.75, '#3a8fc4'],
            [1,    '#1dd4b4']
        ],
        showscale: true
    }];

    // Build the label positions based on continent centers
    let labelLats = [];
    let labelLons = [];
    let labelText = [];

    Object.entries(continents).forEach(([name, value]) => {
        let center = continentCenters[name];
        
        if(!center || value == null || value == undefined) {
            return;
        }
        
        // Convert the prediction value to be used as the label text into a string
        let pred_value = Number(value).toFixed(2)
        
        labelLats.push(center.lat);
        labelLons.push(center.lon);
        
        // Handle both negative and positive temperature anomaly predictions
        if(pred_value >= 0){
            labelText.push("+" + pred_value + "°C")
        } else {
            labelText.push(pred_value + "°C")
        }
        
    });

    mapData.push({
        type: 'scattergeo',
        lat: labelLats,
        lon: labelLons,
        text: labelText,
        mode: 'markers+text',
        textposition: 'middle center',
        textfont: {
            color: '#ffffff',
            size: 11,
            family: 'Comfortaa'
        },
        marker: {
            size: 50,
            color: 'rgba(0, 0, 0, 0.45)',
            line: {
                color: 'rgba(255, 255, 255, 0.2)',
                width: 1
            },
            symbol: 'circle'
        },
        hoverinfo: 'skip',
        showlegend: false
    });
    
    // Configure the layout
    const layout = {
        geo: {
            projection: {
                type: 'natural earth'
            },
            bgcolor: 'rgba(0,0,0,0)',
            showland: true,
            landcolor: '#161B22',
            showocean: true,
            oceancolor: '#0D1117',
            showcountries: false,
            countrywidth: 0.5,
            showlakes: false
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 0, b: 0, l: 0, r: 0 },
        height: 600
    };
    
    // Render the map
    if (document.getElementById('world-map').data) {
        // Update plot if it already exists
        Plotly.react('world-map', mapData, layout, {
            responsive: true,
            displayModeBar: false
        });
    } else {
        // Create new plot on first render
        Plotly.newPlot('world-map', mapData, layout, {
            responsive: true,
            displayModeBar: false
        });
    }
    
    console.log('Map rendered! :)');
}

document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById('monthSlider');
    const sliderDate = document.getElementById('slider-date');

    slider.addEventListener('input', function() {
        loadPredictions(parseInt(slider.value), sliderDate);
    });

    // Load month 0 on page load
    loadPredictions(0, sliderDate);
});

document.addEventListener('DOMContentLoaded', function () {
    const overlay = document.getElementById('loading-overlay');
    const liveForm = document.querySelector('form[action="/analysis/live"]');

    liveForm.addEventListener('submit', function () {
        overlay.classList.add('active');
    });
});