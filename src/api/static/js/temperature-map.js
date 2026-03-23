async function loadPredictions(monthIndex) {
    try {
        console.log(`Fetching month ${monthIndex}...`);
        
        const response = await fetch(`/analysis/predictions/${monthIndex}`);
        const data = await response.json();
        
        console.log('Prediction data:', data);
        
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
    
    // Map all country names to continents... Will be changed later?
    const continentMapping = {
        "Africa": [
            "Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cabo Verde","Cameroon",
            "Central African Republic","Chad","Comoros","Democratic Republic of the Congo",
            "Republic of the Congo","Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini",
            "Ethiopia","Gabon","Gambia","Ghana","Guinea","Guinea-Bissau","Ivory Coast","Kenya",
            "Lesotho","Liberia","Libya","Madagascar","Malawi","Mali","Mauritania","Mauritius",
            "Morocco","Mozambique","Namibia","Niger","Nigeria","Rwanda","Sao Tome and Principe",
            "Senegal","Seychelles","Sierra Leone","Somalia","South Africa","South Sudan","Sudan",
            "Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe"
        ], "Asia": [
            "Afghanistan","Armenia","Azerbaijan","Bahrain","Bangladesh","Bhutan","Brunei",
            "Cambodia","China","Cyprus","Georgia","India","Indonesia","Iran","Iraq","Palestine",
            "Japan","Jordan","Kazakhstan","Kuwait","Kyrgyzstan","Laos","Lebanon","Malaysia",
            "Maldives","Mongolia","Myanmar","Nepal","North Korea","Oman","Pakistan","Palestine",
            "Philippines","Qatar","Saudi Arabia","Singapore","South Korea","Sri Lanka","Syria",
            "Taiwan","Tajikistan","Thailand","Timor-Leste","Turkey","Turkmenistan",
            "United Arab Emirates","Uzbekistan","Vietnam","Yemen","Russia"
        ], "Europe": [
            "Albania","Andorra","Austria","Belarus","Belgium","Bosnia and Herzegovina","Bulgaria",
            "Croatia","Czechia","Denmark","Estonia","Finland","France","Germany","Greece",
            "Hungary","Iceland","Ireland","Italy","Kosovo","Latvia","Liechtenstein","Lithuania",
            "Luxembourg","Malta","Moldova","Monaco","Montenegro","Netherlands","North Macedonia",
            "Norway","Poland","Portugal","Romania","San Marino","Serbia","Slovakia",
            "Slovenia","Spain","Sweden","Switzerland","Ukraine","United Kingdom","Vatican City"
        ], "North America": [
            "Antigua and Barbuda","Bahamas","Barbados","Belize","Canada","Costa Rica","Cuba",
            "Dominica","Dominican Republic","El Salvador","Grenada","Guatemala","Haiti",
            "Honduras","Jamaica","Mexico","Nicaragua","Panama","Saint Kitts and Nevis",
            "Saint Lucia","Saint Vincent and the Grenadines","Trinidad and Tobago",
            "United States","Green Land"
        ], "South America": [
            "Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador","Guyana","Paraguay",
            "Peru","Suriname","Uruguay","Venezuela"
        ], "Oceania": [
            "Australia","Fiji","Kiribati","Marshall Islands","Micronesia","Nauru","New Zealand",
            "Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu"
        ], "Antarctica": ["Antarctica"]
    }
    
    // Assign the continent values to each of their countries
    Object.entries(continents).forEach(([name, value]) => {
        const countries = continentMapping[name];

        if (!countries) return;

        countries.forEach(country => {
            locations.push(country);
            values.push(value);
            text.push(`${name}<br>${value.toFixed(2)}°C`);
        });
    });
    
    // Create the plotly map data
    const mapData = [{
        type: 'choropleth',
        locationmode: 'country names',
        locations: locations,
        z: values,
        text: text,
        hoverinfo: 'text',
        reversescale: false,
        zmin: -4.0,
        zmax: 4.0,
        // showscale: false,
        colorscale: [
            [0,    '#e8d5f5'],
            [0.25, '#a78de8'],
            [0.5,  '#6c63d4'],
            [0.75, '#3a8fc4'],
            [1,    '#1dd4b4']
        ],
        showscale: false // Hide plotly scale to show custom one.
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
    Plotly.newPlot('world-map', mapData, layout, {
        responsive: true,
        displayModeBar: false
    });
    
    console.log('Map rendered! :)');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Starting...');
    loadPredictions(3); // Manually feed in month-index for testing map display. Will change later to actual data
});