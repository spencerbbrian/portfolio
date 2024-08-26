class Casting
{
    public static void main(String a[])
    {
        //CASTING
        int y = 257;
        byte k = (byte) y;
        System.out.println(k); //for a value out of range. 257 will be divided by the range and the output shown.

        float v = 5.6f;
        int w = (int)v;
        System.out.println(w);
    }
}