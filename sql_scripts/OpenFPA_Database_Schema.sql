
-- SQL Script to Create OpenFPA Database Structure

-- Revenues Table
CREATE TABLE revenues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    customer VARCHAR(255) NOT NULL,
    revenue_amount DECIMAL(15, 2) NOT NULL
);

-- Costs Table
CREATE TABLE costs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    cost_type VARCHAR(255) NOT NULL,
    cost_amount DECIMAL(15, 2) NOT NULL
);

-- KPIs Table
CREATE TABLE kpis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kpi_name VARCHAR(255) NOT NULL,
    target_value DECIMAL(5, 2) NOT NULL,
    actual_value DECIMAL(5, 2) NOT NULL
);
