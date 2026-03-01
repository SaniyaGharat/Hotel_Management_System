// Modal functionality
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside
window.onclick = function (event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.getElementsByClassName('alert');
    setTimeout(function () {
        for (let i = 0; i < alerts.length; i++) {
            alerts[i].style.opacity = '0';
            setTimeout(function () {
                alerts[i].style.display = 'none';
            }, 500);
        }
    }, 5000);
});

// Form validation
function validateReservationForm() {
    const checkIn = new Date(document.getElementById('check_in').value);
    const checkOut = new Date(document.getElementById('check_out').value);

    if (checkOut <= checkIn) {
        alert('Check-out date must be after check-in date');
        return false;
    }
    return true;
}

// For billing page - Generate bill details
function generateBill(reservationId) {
    if (!reservationId) {
        alert('Please select a reservation');
        return;
    }

    fetch(`/billing/generate/${reservationId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Update guest information
            document.getElementById('guestName').textContent = data.reservation.guest_name;
            document.getElementById('roomNumber').textContent = data.reservation.room_number;
            document.getElementById('stayDates').textContent = `${data.reservation.check_in} to ${data.reservation.check_out}`;
            document.getElementById('daysStayed').textContent = data.reservation.days;

            // Update room charges
            document.getElementById('roomCharge').textContent = `$${data.room_charge.toFixed(2)}`;

            // Update service charges
            const serviceChargesDiv = document.getElementById('serviceCharges');
            serviceChargesDiv.innerHTML = '';

            if (data.service_orders && data.service_orders.length > 0) {
                data.service_orders.forEach(service => {
                    const serviceDiv = document.createElement('div');
                    serviceDiv.className = 'bill-item';
                    const statusClass = service.status === 'completed' ? 'status-completed' :
                        service.status === 'in progress' ? 'status-in-progress' : 'status-pending';
                    serviceDiv.innerHTML = `
                        <span class="item-name">
                            ${service.service_name} (${service.quantity} x $${service.price.toFixed(2)})
                            <span class="service-status ${statusClass}">${service.status}</span>
                        </span>
                        <span class="item-amount">$${service.total_cost.toFixed(2)}</span>
                    `;
                    serviceChargesDiv.appendChild(serviceDiv);
                });

                // Add service charges total
                const serviceTotalDiv = document.createElement('div');
                serviceTotalDiv.className = 'bill-item service-total';
                serviceTotalDiv.innerHTML = `
                    <span class="item-name">Total Service Charges</span>
                    <span class="item-amount">$${data.service_charge.toFixed(2)}</span>
                `;
                serviceChargesDiv.appendChild(serviceTotalDiv);
            }

            // Update totals
            document.getElementById('totalAmount').textContent = `$${data.total_amount.toFixed(2)}`;
            document.getElementById('paidAmount').textContent = `$${data.paid_amount.toFixed(2)}`;
            document.getElementById('balanceAmount').textContent = `$${data.balance.toFixed(2)}`;
            document.getElementById('hiddenTotalAmount').value = data.total_amount;

            // Show the bill details section
            document.getElementById('billDetails').style.display = 'block';
        })
        .catch(error => {
            console.error('Error generating bill:', error);
            alert('Error generating bill: ' + error.message);
        });
}

// Parse amenities JSON
function parseAmenities(amenitiesString) {
    try {
        return JSON.parse(amenitiesString);
    } catch (e) {
        console.error("Error parsing amenities:", e);
        return {};
    }
}

// Toggle room status quickly
function updateRoomStatus(roomId, newStatus) {
    document.getElementById(`room_status_${roomId}`).value = newStatus;
    document.getElementById(`room_form_${roomId}`).submit();
}

// Filter table rows based on search input
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let visible = false;
        const tds = tr[i].getElementsByTagName("td");

        for (let j = 0; j < tds.length; j++) {
            const td = tds[j];
            if (td) {
                const txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    visible = true;
                    break;
                }
            }
        }

        tr[i].style.display = visible ? "" : "none";
    }
}

// Date utilities
function formatDate(date) {
    const d = new Date(date);
    const month = '' + (d.getMonth() + 1);
    const day = '' + d.getDate();
    const year = d.getFullYear();

    return [year, month.padStart(2, '0'), day.padStart(2, '0')].join('-');
}

function setDefaultDates() {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');

    if (checkInInput && checkOutInput) {
        const today = new Date();
        const tomorrow = new Date();
        tomorrow.setDate(today.getDate() + 1);

        checkInInput.value = formatDate(today);
        checkOutInput.value = formatDate(tomorrow);
    }
}

// Initialize elements on page load
document.addEventListener('DOMContentLoaded', function () {
    // Set default dates for reservation form
    setDefaultDates();

    // Add search functionality to tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function () {
            const tableId = this.getAttribute('data-table');
            filterTable(this.id, tableId);
        });
    });

    // Add event listener for update order buttons
    const updateButtons = document.querySelectorAll('.update-order-btn');
    updateButtons.forEach(button => {
        button.addEventListener('click', function () {
            try {
                const orderData = JSON.parse(this.dataset.order);
                openUpdateOrderModal(orderData);
            } catch (error) {
                console.error('Error parsing order data:', error);
                alert('Error opening update modal');
            }
        });
    });

    // Add event listener for form submission
    const updateOrderForm = document.getElementById('updateOrderForm');
    if (updateOrderForm) {
        updateOrderForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        window.location.reload();
                    } else {
                        throw new Error(data.error || 'Failed to update service order');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error updating service order: ' + error.message);
                });
        });
    }
});

function openUpdateOrderModal(order) {
    const modal = document.getElementById('updateOrderModal');
    const form = document.getElementById('updateOrderForm');
    const orderDetails = document.getElementById('order_details');
    const statusSelect = document.getElementById('update_status');

    if (!modal || !form || !orderDetails || !statusSelect) {
        console.error('Required modal elements not found');
        return;
    }

    // Update order details
    orderDetails.innerHTML = `
        <strong>Guest:</strong> ${order.guest_name}<br>
        <strong>Room:</strong> ${order.room_number}<br>
        <strong>Service:</strong> ${order.service_name} ($${order.price})<br>
        <strong>Quantity:</strong> ${order.quantity}<br>
        <strong>Current Status:</strong> ${order.status}
    `;

    // Set current status in select
    statusSelect.value = order.status;

    // Update form action
    form.action = `/service_orders/update/${order.id}`;

    // Show modal
    modal.style.display = 'block';
}

function openEditRoomModal(roomId) {
    try {
        // Fetch room data
        fetch(`/rooms/get/${roomId}`)
            .then(response => response.json())
            .then(room => {
                const modal = document.getElementById('editRoomModal');
                const form = document.getElementById('editRoomForm');

                if (!modal || !form) {
                    throw new Error('Modal or form not found');
                }

                // Set form action
                form.action = `/rooms/update/${room.id}`;

                // Set form values
                document.getElementById('edit_room_type').value = room.room_type;
                document.getElementById('edit_capacity').value = room.capacity;
                document.getElementById('edit_price').value = room.price;
                document.getElementById('edit_status').value = room.status;

                // Set amenities checkboxes
                let amenities;
                try {
                    amenities = typeof room.amenities === 'string' ? JSON.parse(room.amenities) : room.amenities;
                } catch (e) {
                    console.error('Error parsing amenities:', e);
                    amenities = {};
                }

                document.getElementById('edit_wifi').checked = amenities.wifi || false;
                document.getElementById('edit_tv').checked = amenities.tv || false;
                document.getElementById('edit_ac').checked = amenities.ac || false;
                document.getElementById('edit_minibar').checked = amenities.minibar || false;
                document.getElementById('edit_jacuzzi').checked = amenities.jacuzzi || false;
                document.getElementById('edit_balcony').checked = amenities.balcony || false;

                // Show modal
                modal.style.display = 'block';
            })
            .catch(error => {
                console.error('Error fetching room data:', error);
                alert('Error opening edit modal: ' + error.message);
            });
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    }
}

// Add event listener for form submission
document.addEventListener('DOMContentLoaded', function () {
    const editRoomForm = document.getElementById('editRoomForm');
    if (editRoomForm) {
        editRoomForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(this);

            fetch(this.action, {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        window.location.reload();
                    } else {
                        throw new Error(data.error || 'Failed to update room');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error updating room: ' + error.message);
                });
        });
    }
});

// ==================== NEW FEATURE JS ====================

// Notifications Toggle
function toggleNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        return;
    }

    // Fetch notifications
    fetch('/notifications')
        .then(r => r.json())
        .then(data => {
            let html = '<div class="notification-dropdown-header">' +
                '<h3>Notifications</h3>' +
                '<button class="btn btn-sm btn-secondary" onclick="markAllRead()">Mark all read</button>' +
                '</div>';

            if (data.length === 0) {
                html += '<div class="notification-empty">No notifications</div>';
            } else {
                data.forEach(n => {
                    const unread = !n.is_read ? 'unread' : '';
                    const time = new Date(n.created_at).toLocaleString();
                    html += `<div class="notification-item ${unread}" onclick="markRead(${n.id}, this)">
                        <div class="notif-title">${n.title}</div>
                        <div class="notif-message">${n.message}</div>
                        <div class="notif-time">${time}</div>
                    </div>`;
                });
            }

            dropdown.innerHTML = html;
            dropdown.classList.add('show');
        })
        .catch(err => console.error('Error fetching notifications:', err));
}

function markRead(id, element) {
    fetch(`/notifications/read/${id}`, { method: 'POST' })
        .then(() => {
            if (element) element.classList.remove('unread');
            // Update badge
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                const count = parseInt(badge.textContent) - 1;
                if (count <= 0) badge.style.display = 'none';
                else badge.textContent = count;
            }
        });
}

function markAllRead() {
    fetch('/notifications/read-all', { method: 'POST' })
        .then(() => {
            document.querySelectorAll('.notification-item.unread').forEach(el => el.classList.remove('unread'));
            const badge = document.querySelector('.notification-badge');
            if (badge) badge.style.display = 'none';
        });
}

// Close notifications when clicking outside
document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('notificationDropdown');
    if (dropdown && !e.target.closest('.notification-bell')) {
        dropdown.classList.remove('show');
    }
});

// Staff Edit Modal
function openEditStaffModal(id) {
    fetch(`/staff/get/${id}`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('edit_name').value = data.name;
            document.getElementById('edit_email').value = data.email;
            document.getElementById('edit_phone').value = data.phone || '';
            document.getElementById('edit_role').value = data.role;
            document.getElementById('edit_shift').value = data.shift;
            document.getElementById('edit_salary').value = data.salary;
            document.getElementById('edit_staff_status').value = data.status;

            const form = document.getElementById('editStaffForm');
            form.action = `/staff/update/${id}`;

            form.onsubmit = function (e) {
                e.preventDefault();
                const formData = new FormData(form);

                fetch(`/staff/update/${id}`, {
                    method: 'POST',
                    body: formData
                })
                    .then(r => r.json())
                    .then(result => {
                        if (result.message) {
                            closeModal('editStaffModal');
                            window.location.reload();
                        } else {
                            alert(result.error || 'Update failed');
                        }
                    })
                    .catch(err => alert('Error: ' + err.message));
            };

            openModal('editStaffModal');
        })
        .catch(err => alert('Error loading staff data: ' + err.message));
}

// Reservation Edit Modal
function openEditReservationModal(reservation) {
    document.getElementById('edit_guest_name').value = reservation.guest_name;
    document.getElementById('edit_room_number').value = reservation.room_number + ' (' + reservation.room_type + ')';
    document.getElementById('edit_status').value = reservation.status;
    document.getElementById('edit_payment_status').value = reservation.payment_status;

    const form = document.getElementById('editReservationForm');
    form.action = '/reservations/update/' + reservation.id;

    openModal('editReservationModal');
}
