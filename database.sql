CREATE DATABASE IF NOT EXISTS hospital_ecommerce;
USE hospital_ecommerce;

CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 email VARCHAR(120) UNIQUE NOT NULL,
 password VARCHAR(255) NOT NULL,
 role ENUM('patient','admin') DEFAULT 'patient',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doctors (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 specialization VARCHAR(100) NOT NULL,
 phone VARCHAR(20),
 email VARCHAR(120),
 available_days VARCHAR(100),
 fee DECIMAL(10,2) DEFAULT 500
);

CREATE TABLE IF NOT EXISTS medicines (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(150) NOT NULL,
 category VARCHAR(100) NOT NULL,
 description TEXT,
 price DECIMAL(10,2) NOT NULL,
 stock INT DEFAULT 0,
 image VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS appointments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 doctor_id INT NOT NULL,
 appointment_date DATE NOT NULL,
 appointment_time TIME NOT NULL,
 message TEXT,
 status ENUM('Pending','Approved','Completed','Cancelled') DEFAULT 'Pending',
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_id INT NOT NULL,
 total_amount DECIMAL(10,2) NOT NULL,
 address TEXT NOT NULL,
 payment_method ENUM('COD','Online Demo') DEFAULT 'COD',
 status ENUM('Pending','Confirmed','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
 id INT AUTO_INCREMENT PRIMARY KEY,
 order_id INT NOT NULL,
 medicine_id INT NOT NULL,
 quantity INT NOT NULL,
 price DECIMAL(10,2) NOT NULL,
 FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
 FOREIGN KEY(medicine_id) REFERENCES medicines(id)
);

INSERT IGNORE INTO doctors(name,specialization,phone,email,available_days,fee) VALUES
('Dr. Amit Sharma','General Physician','9876543210','amit@medicare.com','Mon-Fri',500),
('Dr. Priya Verma','Cardiologist','9876543211','priya@medicare.com','Tue-Sat',800),
('Dr. Rahul Patil','Dermatologist','9876543212','rahul@medicare.com','Mon-Sat',700),
('Dr. Neha Joshi','Pediatrician','9876543213','neha@medicare.com','Mon-Fri',600);

INSERT IGNORE INTO medicines(name,category,description,price,stock,image) VALUES
('Paracetamol 500mg','Tablets','For fever and mild pain.','25.00',100,'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600'),
('Vitamin C Tablets','Vitamins','Vitamin supplement product.','120.00',80,'https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=600'),
('Cough Syrup','Syrup','General cough relief product.','80.00',50,'/static/images/cough-syrup.svg'),
('First Aid Kit','First Aid','Basic first aid supplies.','250.00',30,'https://images.unsplash.com/photo-1603398938378-e54eab446dde?w=600'),
('ORS Sachets','Health Care','Oral rehydration solution.','20.00',100,'/static/images/ors-sachets.svg'),
('Digital Thermometer','Devices','Digital body thermometer.','180.00',25,'/static/images/digital-thermometer.svg');

UPDATE medicines
SET image='/static/images/digital-thermometer.svg'
WHERE name='Digital Thermometer'
  AND image='https://images.unsplash.com/photo-1584634731339-252c581abfc5?w=600';

UPDATE medicines
SET image='/static/images/ors-sachets.svg'
WHERE name='ORS Sachets';

UPDATE medicines
SET image='/static/images/cough-syrup.svg'
WHERE name='Cough Syrup';
