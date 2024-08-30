class Computer
{
    public void playMusic() //void - return nothing back
    {
        System.out.println("Music Playing");
    }

    public String getMeAPen(int cost)
    {
        if(cost >= 10)
            return "Pen";
        else
            return "Nothing";
    }
}

class Engine //different methods but same name.
{
    public int add(int n1, int n2, int n3)
    {
        return n1 + n2 + n3;
    }

    public int add(int n1, int n2)
    {
        return n1 + n2;
    }

    public double add(double n1, int n2)
    {
        return n1 + n2;
    }
}


public class methods 
{
    public static void main(String[] args)
    {
        Computer obj = new Computer();
        obj.playMusic();
        String str = obj.getMeAPen(2);
        System.out.println(str);

        Engine obj2 = new Engine();
        double r1 = obj2.add(3.5, 4);
        System.out.println(r1);
    }    
}
