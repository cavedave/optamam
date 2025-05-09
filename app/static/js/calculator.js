// Global variables to store state
let peopleNames = [];
let itemNames = [];
let valuations = {};
let divisibleFlags = {};

function getFormData() {
    return {
        items: itemNames.map(name => ({
            name: name,
            is_divisible: divisibleFlags[name]
        })),
        people: peopleNames,
        valuations: valuations
    };
}

function proceedToValuation() {
    // Get and parse input values
    peopleNames = document.getElementById('people-names').value.split(',').map(name => name.trim());
    itemNames = document.getElementById('item-names').value.split(',').map(item => item.trim());
    
    // Validate inputs
    if (peopleNames.length === 0 || itemNames.length === 0) {
        alert('Please enter both people and item names');
        return;
    }
    
    // Hide header section and show valuation section
    document.getElementById('header-section').style.display = 'none';
    document.getElementById('valuation-section').style.display = 'block';
    
    // Generate valuation form
    generateValuationForm();
}

function generateValuationForm() {
    const formDiv = document.getElementById('valuation-form');
    formDiv.innerHTML = '';
    
    // Initialize valuations object with default values
    itemNames.forEach(item => {
        valuations[item] = {};
        peopleNames.forEach(person => {
            valuations[item][person] = 10;  // Default value
        });
    });
    
    // Initialize divisible flags with first item as divisible
    itemNames.forEach((item, index) => {
        divisibleFlags[item] = index === 0;  // First item is divisible by default
    });
    
    itemNames.forEach((item, itemIndex) => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'card mb-3';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Item header with divisible flag
        const headerDiv = document.createElement('div');
        headerDiv.className = 'd-flex justify-content-between align-items-center mb-3';
        
        const title = document.createElement('h5');
        title.className = 'card-title mb-0';
        title.textContent = `Item: ${item}`;
        
        const divisibleDiv = document.createElement('div');
        divisibleDiv.className = 'form-check';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = `divisible-${itemIndex}`;
        checkbox.checked = divisibleFlags[item];  // Set initial state
        checkbox.onchange = (e) => {
            divisibleFlags[item] = e.target.checked;
        };
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `divisible-${itemIndex}`;
        label.textContent = 'Divisible';
        
        divisibleDiv.appendChild(checkbox);
        divisibleDiv.appendChild(label);
        
        headerDiv.appendChild(title);
        headerDiv.appendChild(divisibleDiv);
        
        // Valuation inputs for each person
        const valuationsDiv = document.createElement('div');
        valuationsDiv.className = 'row';
        
        peopleNames.forEach((person, personIndex) => {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-2';
            
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';
            
            const input = document.createElement('input');
            input.type = 'number';
            input.className = 'form-control';
            input.min = '0';
            input.value = valuations[item][person];  // Use the initialized value
            input.onchange = (e) => {
                valuations[item][person] = parseInt(e.target.value);
            };
            
            const label = document.createElement('span');
            label.className = 'input-group-text';
            label.textContent = person;
            
            inputGroup.appendChild(label);
            inputGroup.appendChild(input);
            col.appendChild(inputGroup);
            valuationsDiv.appendChild(col);
        });
        
        cardBody.appendChild(headerDiv);
        cardBody.appendChild(valuationsDiv);
        itemDiv.appendChild(cardBody);
        formDiv.appendChild(itemDiv);
    });
}

async function calculateFairDivision() {
    try {
        const formData = getFormData();
        
        // Convert form data to the new API format
        const requestData = {
            items: formData.items.map(item => ({
                name: item.name,
                is_divisible: item.is_divisible
            })),
            people: formData.people.map(person => ({
                name: person
            })),
            valuations: []
        };

        // Add valuations
        formData.items.forEach(item => {
            formData.people.forEach(person => {
                requestData.valuations.push({
                    person: person,
                    item: item.name,
                    value: parseFloat(formData.valuations[item.name][person]) || 0
                });
            });
        });

        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Calculation failed');
        }

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Calculation failed');
        }

        displayResults(result.result);
    } catch (error) {
        console.error('Error:', error);
        alert(error.message);
    }
}

function displayResults(result) {
    const resultsDiv = document.getElementById('results-content');
    resultsDiv.innerHTML = '';
    
    // Display worst satisfaction
    const satisfactionDiv = document.createElement('div');
    satisfactionDiv.className = 'alert alert-info';
    satisfactionDiv.textContent = `Worst satisfaction value: ${result.worst_satisfaction.toFixed(1)}%`;
    resultsDiv.appendChild(satisfactionDiv);
    
    // Display allocations
    const table = document.createElement('table');
    table.className = 'table table-striped';
    
    // Table header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Person</th>
            <th>Indivisible Items</th>
            <th>Divisible Items</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // Table body
    const tbody = document.createElement('tbody');
    for (const [person, allocation] of Object.entries(result.allocations)) {
        const row = document.createElement('tr');
        
        // Person name
        const nameCell = document.createElement('td');
        nameCell.textContent = person;
        
        // Indivisible items
        const indivisibleCell = document.createElement('td');
        const indivisibleItems = Object.entries(allocation.indivisible)
            .filter(([_, value]) => value === 1)
            .map(([item, _]) => item)
            .join(', ');
        indivisibleCell.textContent = indivisibleItems || 'None';
        
        // Divisible items
        const divisibleCell = document.createElement('td');
        const divisibleItems = Object.entries(allocation.divisible)
            .map(([item, value]) => `${item}: ${(value * 100).toFixed(1)}%`)
            .join(', ');
        divisibleCell.textContent = divisibleItems || 'None';
        
        row.appendChild(nameCell);
        row.appendChild(indivisibleCell);
        row.appendChild(divisibleCell);
        tbody.appendChild(row);
    }
    table.appendChild(tbody);
    resultsDiv.appendChild(table);
    
    // Show results section
    document.getElementById('results-section').style.display = 'block';
}

function downloadResults() {
    // Create CSV content
    let csvContent = 'Person,Indivisible Items,Divisible Items\n';
    
    const resultsDiv = document.getElementById('results-content');
    const table = resultsDiv.querySelector('table');
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        csvContent += `${cells[0].textContent},"${cells[1].textContent}","${cells[2].textContent}"\n`;
    });
    
    // Create and trigger download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fair_division_results.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
} 