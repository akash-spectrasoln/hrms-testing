


function toggleLoadingOverlay(showOverlay) {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        if (showOverlay) {
            loadingOverlay.style.display = 'block';
        } else {
            loadingOverlay.style.display = 'none';
        }
    }
}

// Hide loading overlay when the page is being shown
window.addEventListener('pageshow', function(event) {
    toggleLoadingOverlay(false);
});

// Show loading overlay when the form is submitted and the form is valid
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    // Function to validate form fields
    function validateForm() {
        const inputs = form.querySelectorAll('input[required]');
        for (let i = 0; i < inputs.length; i++) {
            if (!inputs[i].value) {
                return false; // Return false if any required field is empty
            }
        }
        return true; // Return true if all required fields are filled
    }

    // Show loading overlay when the form is submitted and the form is valid
    form.addEventListener('submit', function(event) {
        if (validateForm()) {
            toggleLoadingOverlay(true);
        } else {
            event.preventDefault(); // Prevent form submission if validation fails
        }
    });

    // Hide loading overlay when the prompt is displayed
    const promptButton = document.getElementById('addDestinationButton');
    if (promptButton) {
        promptButton.addEventListener('click', function() {
            toggleLoadingOverlay(false);
        });
    }
});

// Show loading overlay when the page is being refreshed
window.addEventListener('beforeunload', function() {
    toggleLoadingOverlay(true);
});

// Hide loading overlay when the page finishes loading
window.addEventListener('load', function() {
    toggleLoadingOverlay(false);
});



// toggle button  in each connection pages
function toggleConnection(connection_id, status) {
    $.ajax({
        url: `/toggle/${connection_id}/?status=${status}`,
        method: 'GET',
        success: function(data) {
            const isActive = data.is_active;
            $('#status-' + connection_id).text(isActive === 'A' ? 'Active' : 'Paused');
            $('#connectionStatus').html(isActive === 'A' ? '<span style="color: green;">Active</span>' : '<span style="color: gray;">Paused</span>');
            $('#toggleConnection').prop('checked', isActive === 'A');
            $('.custom-control-label').html(isActive === 'A' ? '<span class="text-success">Active</span>' : '<span class="text-info">Paused</span>');

            // Show or hide the "Next Sync in" information based on status
            if (isActive === 'A') {
                $('#nextSyncInfo').show();
            } else {
                $('#nextSyncInfo').hide();
            }
        }
    });
}






// search js code
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const tableList = document.getElementById('tablelist');
    
    if (searchInput && tableList) {
        searchInput.addEventListener('input', function() {
            var searchQuery = this.value.toLowerCase();
            var tableRows = tableList.querySelectorAll('tbody tr');

            // Loop through each table row
            tableRows.forEach(function(row) {
                var firstCell = row.querySelector('td');
                if (firstCell) {
                    var tableName = firstCell.textContent.toLowerCase();

                    // Check if the table name contains the search query
                    if (tableName.includes(searchQuery)) {
                        row.style.display = 'table-row'; // Show the table row
                    } else {
                        row.style.display = 'none'; // Hide the table row
                    }
                }
            });
        });
    }
});

 