class Mobile 
{
    String brand;
    int price;
    String name;

    // static String name; //this string will cause the name variable to be consistent in all objects if changed

    public void show()
    {
        System.out.println(brand + " : " + price + " : " +name);
    }
}

public class string_buffer {
    public static void main(String[] args) {
        
        Mobile obj1 = new Mobile();
        obj1.brand = "Apple";
        obj1.price = 1500;
        obj1.name = "SmartPhone";

        Mobile obj2 = new Mobile();
        obj2.brand = "Samsung";
        obj2.price = 1700;
        obj2.name = "SmartPhone";

        obj1.name = "Phone";
        obj1.show();
        obj2.show();
    }
}
