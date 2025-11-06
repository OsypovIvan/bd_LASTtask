DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    event_date DATE,
    price NUMERIC(6,2),
    available_tickets INT,
    status VARCHAR(20) DEFAULT 'Available'
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    buyer_name VARCHAR(100),
    purchase_date TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION decrease_tickets()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE events
    SET available_tickets = available_tickets - 1
    WHERE id = NEW.event_id;

    UPDATE events
    SET status = 'Sold out'
    WHERE id = NEW.event_id AND available_tickets <= 0;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_decrease_tickets
AFTER INSERT ON tickets
FOR EACH ROW
EXECUTE FUNCTION decrease_tickets();

CREATE OR REPLACE FUNCTION prevent_double_purchase()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM tickets WHERE event_id = NEW.event_id AND buyer_name = NEW.buyer_name) THEN
        RAISE EXCEPTION 'You have already bought a ticket for this event!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_double_purchase
BEFORE INSERT ON tickets
FOR EACH ROW
EXECUTE FUNCTION prevent_double_purchase();
