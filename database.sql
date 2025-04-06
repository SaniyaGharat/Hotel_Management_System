-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS hotel_management3;
USE hotel_management3;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'receptionist', 'staff') NOT NULL DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create default admin user
INSERT INTO users (name, email, password, role) VALUES 
('Admin', 'admin@hotel.com', 'admin123', 'admin');

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_type ENUM('Standard', 'Deluxe', 'Suite', 'Executive') NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    price DECIMAL(10, 2) NOT NULL,
    amenities JSON,
    status ENUM('Available', 'Occupied', 'Maintenance') NOT NULL DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample room data
INSERT INTO rooms (room_number, room_type, capacity, price, amenities, status) VALUES
('101', 'Standard', 2, 99.99, '{"wifi": true, "tv": true, "ac": true}', 'Available'),
('102', 'Standard', 2, 99.99, '{"wifi": true, "tv": true, "ac": true}', 'Available'),
('201', 'Deluxe', 2, 149.99, '{"wifi": true, "tv": true, "ac": true, "minibar": true}', 'Available'),
('202', 'Deluxe', 3, 159.99, '{"wifi": true, "tv": true, "ac": true, "minibar": true}', 'Available'),
('301', 'Suite', 4, 249.99, '{"wifi": true, "tv": true, "ac": true, "minibar": true, "jacuzzi": true}', 'Available'),
('302', 'Suite', 4, 249.99, '{"wifi": true, "tv": true, "ac": true, "minibar": true, "jacuzzi": true}', 'Available'),
('401', 'Executive', 2, 299.99, '{"wifi": true, "tv": true, "ac": true, "minibar": true, "jacuzzi": true, "balcony": true}', 'Available');

-- Reservations table
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    guest_name VARCHAR(100) NOT NULL,
    guest_email VARCHAR(100) NOT NULL,
    guest_phone VARCHAR(20),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    adults INT NOT NULL DEFAULT 1,
    children INT NOT NULL DEFAULT 0,
    status ENUM('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled') NOT NULL DEFAULT 'pending',
    payment_status ENUM('pending', 'partial', 'paid') NOT NULL DEFAULT 'pending',
    payment_amount DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);

-- Services table for additional hotel services
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample services
INSERT INTO services (service_name, description, price, available) VALUES
('Room Service', 'Food and beverages delivered to room', 15.00, TRUE),
('Spa Treatment', 'Relaxing spa treatments', 80.00, TRUE),
('Airport Shuttle', 'Transportation to/from airport', 25.00, TRUE),
('Laundry', 'Laundry and dry cleaning services', 20.00, TRUE);

-- Service orders table
CREATE TABLE IF NOT EXISTS service_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    service_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'in progress', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
    notes TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('cash', 'credit_card', 'debit_card', 'bank_transfer') NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'paid', 'refunded') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);
