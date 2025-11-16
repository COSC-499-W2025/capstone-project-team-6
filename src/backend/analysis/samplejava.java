/**
 * OOP Example 
 */

import java.util.*;

// Interface
interface Aircraft { void fly(); void land(); }

// Abstract class
abstract class Airplane implements Aircraft {
    private String model; 
    protected String airline; 
    protected int capacity;

    public Airplane(String model, String airline, int capacity) {
        this.model = model; this.airline = airline; this.capacity = capacity;
    }
    public String getModel() { return model; }
    public String getAirline() { return airline; }
    public int getCapacity() { return capacity; }

    public abstract void refuel();
    public void taxi() { System.out.println(model + " (" + airline + ") taxiing to runway"); }
}
class AirbusA320 extends Airplane {
    public AirbusA320(String airline, int cap) { super("Airbus A320", airline, cap); }
    public void fly() { System.out.println(getModel()+" by "+getAirline()+" cruising at 37,000 ft"); }
    public void land() { System.out.println(getModel()+" landing smoothly"); }
    public void refuel() { System.out.println(getModel()+" refueled with Jet-A1"); }
}

class Boeing787 extends Airplane {
    public Boeing787(String airline, int cap) { super("Boeing 787 Dreamliner", airline, cap); }
    public void fly() { System.out.println(getModel()+" by "+getAirline()+" on transatlantic flight"); }
    public void land() { System.out.println(getModel()+" touches down after long-haul journey"); }
    public void refuel() { System.out.println(getModel()+" refueled for next flight"); }
}

class Helicopter extends Airplane {
    public Helicopter(String airline, int cap) { super("Airbus H145", airline, cap); }
    public void fly() { System.out.println(getModel()+" ("+getAirline()+") hovering at 500m"); }
    public void land() { System.out.println(getModel()+" performing vertical landing"); }
    public void refuel() { System.out.println(getModel()+" topped up with aviation turbine fuel"); }
}
class Hangar<T> {
    private T aircraft;
    public void store(T a) { aircraft = a; }
    public T retrieve() { return aircraft; }
}

// Singleton
class AirTrafficControl {
    private static AirTrafficControl instance;
    private String location = "Toronto ATC";
    private AirTrafficControl() {}
    public static AirTrafficControl getInstance() {
        if (instance == null) instance = new AirTrafficControl();
        return instance;
    }
    public void authorizeTakeoff(Airplane a) {
        System.out.println(location + ": Cleared for takeoff -> " + a.getModel() + " (" + a.getAirline() + ")");
    }
}

// Builder
class Passenger {
    private String name, passport, seat, airline;
    private Passenger(Builder b){ name=b.name; passport=b.passport; seat=b.seat; airline=b.airline; }
    public String getName(){ return name; }
    public String getAirline(){ return airline; }

    public static class Builder {
        private String name, passport, seat, airline;
        public Builder name(String n){ name=n; return this; }
        public Builder passport(String p){ passport=p; return this; }
        public Builder seat(String s){ seat=s; return this; }
        public Builder airline(String a){ airline=a; return this; }
        public Passenger build(){ return new Passenger(this); }
    }
}
interface PassengerRepository {
    Passenger findById(Long id); 
    void save(Passenger p);
}

class InMemoryPassengerRepo implements PassengerRepository {
    private Map<Long, Passenger> db = new HashMap<>();
    public Passenger findById(Long id){ return db.get(id); }
    public void save(Passenger p){ db.put((long)(db.size()+1), p); }
}

class PassengerService {
    private PassengerRepository repo;
    public PassengerService(PassengerRepository r){ repo=r; }
    public void register(Passenger p){ System.out.println("Registering "+p.getName()+" ("+p.getAirline()+")"); repo.save(p); }
}

// Enum
enum FlightStatus { BOARDING, ON_TIME, DELAYED, CANCELLED }

// Functional Interface
@FunctionalInterface interface FuelCalculator { int estimate(int pax, int distKm); }

public class samplejava {
    public static void main(String[] args) {
        // Lambda
        FuelCalculator calc = (pax, dist) -> pax * dist / 15;
        System.out.println("Fuel required: " + calc.estimate(200, 5000) + " L");

        // Builder
        Passenger p = new Passenger.Builder()
            .name("John Doe").passport("AB123456").seat("42K").airline("Air Canada").build();

        PassengerService service = new PassengerService(new InMemoryPassengerRepo());
        service.register(p);

        // Singleton
        AirTrafficControl atc = AirTrafficControl.getInstance();

        // Aircraft examples
        List<Airplane> fleet = Arrays.asList(
            new AirbusA320("Air Canada",180),
            new Boeing787("Etihad",250),
            new Helicopter("Rescue BC",4)
        );

        // Demonstrate polymorphism
        for (Airplane plane : fleet) {
            atc.authorizeTakeoff(plane);
            plane.taxi();
            plane.fly();
            plane.refuel();
            plane.land();
            System.out.println("---");
        }

        // Generic class
        Hangar<Airplane> hangar = new Hangar<>();
        hangar.store(fleet.get(0));
        System.out.println("Hangar stores: " + hangar.retrieve().getModel());

        // Enum usage
        FlightStatus status = FlightStatus.ON_TIME;
        System.out.println("Flight status: " + status);
    }
}
