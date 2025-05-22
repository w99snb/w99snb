document.addEventListener('DOMContentLoaded', function() {

    // 1. Sample Network Data
    const networkData = [
        // Nodes
        { data: { id: 'J1', type: 'junction' }, position: { x: 50, y: 50 } },
        { data: { id: 'J2', type: 'junction' }, position: { x: 250, y: 50 } },
        { data: { id: 'T1', type: 'tank' }, position: { x: 150, y: 150 } },
        { data: { id: 'J3', type: 'junction' }, position: { x: 350, y: 150 } }
    ];

    const linkData = [
        // Links (Edges)
        { data: { id: 'P1', source: 'J1', target: 'J2' } },
        { data: { id: 'P2', source: 'J2', target: 'T1' } },
        { data: { id: 'P3', source: 'T1', target: 'J3' } },
        { data: { id: 'P4', source: 'J2', target: 'J3' } }
    ];

    const allElements = networkData.concat(linkData);

    // 2. Cytoscape Initialization
    const cy = cytoscape({
        container: document.getElementById('cy'), // container to render in

        elements: allElements, // list of graph elements (nodes and edges)

        style: [ // the stylesheet for the graph
            {
                selector: 'node',
                style: {
                    'background-color': '#666',
                    'label': 'data(id)',
                    'width': '30px',
                    'height': '30px',
                    'text-valign': 'bottom',
                    'text-halign': 'center',
                    'font-size': '10px',
                    'color': '#000',
                    'text-outline-width': 1,
                    'text-outline-color': '#fff'
                }
            },
            {
                selector: 'node[type = "tank"]', // Selector for tanks based on 'type' data
                style: {
                    'background-color': '#007bff', // Blue color for tanks
                    'shape': 'rectangle'
                }
            },
            {
                selector: 'node[id = "J1"]', // Specific style for J1 if needed initially
                style: {
                    // 'border-width': 2,
                    // 'border-color': 'magenta'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc',
                    // 'target-arrow-shape': 'triangle', // Example for directed edges
                    'curve-style': 'bezier',
                    'label': 'data(id)',
                    'font-size': '8px',
                    'color': '#555',
                    'text-rotation': 'autorotate'
                }
            }
        ],

        layout: {
            name: 'preset' // Uses the 'position' data in nodes
        }
    });

    // 3. Event Handlers for Buttons
    const changeNodeColorBtn = document.getElementById('changeNodeColorBtn');
    const changeLinkStyleBtn = document.getElementById('changeLinkStyleBtn');

    changeNodeColorBtn.addEventListener('click', function() {
        const nodeJ1 = cy.$id('J1');
        if (nodeJ1.length > 0) { // Check if the node exists
            nodeJ1.style('background-color', 'red');
            nodeJ1.style('color', '#fff'); // Change text color for better contrast
            nodeJ1.style('text-outline-color', 'red');
            console.log("Changed color of Node J1 to red.");
        } else {
            console.log("Node J1 not found.");
        }
    });

    changeLinkStyleBtn.addEventListener('click', function() {
        const linkP1 = cy.$id('P1');
        if (linkP1.length > 0) { // Check if the link exists
            linkP1.style({
                'line-color': 'green',
                'width': 5,
                'target-arrow-color': 'green' // if using arrows
            });
            console.log("Changed style of Link P1 to green, width 5.");
        } else {
            console.log("Link P1 not found.");
        }
    });

    console.log("Cytoscape initialized with sample network.");
    // You can also fit the graph to the viewport if needed
    // cy.fit();
});
