class Hello
{
    public static void main(String a[])
    {
        int num1 = 3;
        int num2 = 5;
        int result = num1 + num2;
        System.out.println(num1 + num2);
        System.out.println(result);
        byte by = 127;
        short sh = 558;
        long l = 5854l;
        double d = 5.8;
        char c = 'K';
        boolean b = true;
        System.out.println(result);
        float num = 5.6f; //Always specify f for float else it will be considereda double
        System.out.println(num);
        System.out.println(c);
        System.out.println(by);
        System.out.println(sh);
        System.out.println(l);
        System.out.println(d);
        System.out.println(b);

        //CASTING
        int y = 257;
        byte k = (byte) y;
        System.out.println(k); //for a value out of range. 257 will be divided by the range and the output shown.

        float v = 5.6f;
        int w = (int)v;
        System.out.println(w);
    }
}