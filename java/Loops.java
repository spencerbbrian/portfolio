public class Loops {
    
    public static void main(String[] args) {

        //repeat this statement 4 times
        //loop - while, do while, for

        //while
        // int i = 5;
        // while(i <= 4)
        // {
        //     System.out.println("Hi " + i);
        //     int j = 1;
        //     while(j <= 3){
        //         System.out.println("Hello");
        //         j++;
        //     }
        //     i++;
        // }

        //do-while
        // int i = 5;
        // do{
        //     System.out.println("Hi" + i);
        //     i ++;
        // }
        // while(i<=4);

        //for
        for(int i=1;i<=5;i++)
        {
            System.out.println("DAY " + i);
            for(int j=1;j<=9;j++)
            {
                System.out.println("  " + (j+8) +" - " + (j+9));
            }
        }

    }
}
