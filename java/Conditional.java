class Conditional
{
    public static void main(String[] args)
    {
        // int x = 8;
        // int y = 17;
        // int z = 9;

        // if(x < y && x >20) 
        // {
        //         System.out.println("Hello");
        // }
        // else 
        //     System.out.println("Bye");     


        // if(x>y && x>z)
        // {
        //     System.out.println(x);
        //     System.out.println("Thank you");
        // }
        // else if(y>x && y>z)
        //     System.out.println(y);
        // else
        //     System.out.println(z);

        int n = 5;
        int result = 0;

        if (n%2==0)
            result = 10;
        else
            result = 20;
        System.out.println(result);

        result = n%2==0? 10 : 20; // Reduce code to this
        System.out.println(result);

    }
}