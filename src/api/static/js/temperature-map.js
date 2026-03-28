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
    const text = [];
    
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
            "MMR","NPL","PRK","OMN","PAK","PHL","QAT","SAU","SGP","KOR","LKA","SYR","TWN",
            "TJK","THA","TLS","TUR","TKM","ARE","UZB","VNM","YEM"
        ],
        "Europe": [
            "ALB","AND","AUT","BLR","BEL","BIH","BGR","HRV","CZE","DNK","EST","FIN","FRA",
            "DEU","GRC","HUN","ISL","IRL","ITA","XKX","LVA","LIE","LTU","LUX","MLT","MDA",
            "MCO","MNE","NLD","MKD","NOR","POL","PRT","ROU","RUS","SMR","SRB","SVK","SVN",
            "ESP","SWE","CHE","UKR","GBR","VAT"
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
    }
    
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
        text: text,
        hoverinfo: 'text',
        reversescale: false,
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
            countrycolor: '#30363D',
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