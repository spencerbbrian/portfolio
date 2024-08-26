class Assign_ops {
    
    public static void main(String args[])
    {
        int num1 = 7;
        int num2 = 5;

        int result = num1 % num2;
        System.out.println(result); 

        int num3 = 5;
        num3 *= 2;
        System.out.println(num3);

        int num4 = 2;
        int result1 = num4++; //post-increment (fetch first and increment)
        System.out.println(result1);

        int num5 = 2;
        int result2 = ++num5; //pre-increment (increment and fetch)
        System.out.println(result2);
    }
}
