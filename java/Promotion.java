class Promotion
{
    public static void main(String args[])
    {
        byte a = 10;
        byte b = 20;

        int result = a * b; //Since 10*20 is out of byte range, it is promoted to the next

        System.out.println(result);
    }
}