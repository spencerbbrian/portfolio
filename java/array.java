

public class array {
    public static void main(String[] args)
    {

        int fishes[][] = new int [3][]; //jagged
        fishes[0] = new int[3];
        fishes[1] = new int[4];
        fishes[2] = new int[2]; 

        for(int i=0;i<fishes.length;i++)
        {
            for(int j=0;j<fishes[i].length;j++)
            {
                fishes[i][j] = (int)(Math.random() * 10);
            }
        }

        for(int n[]: fishes)
        {
            for(int m: n)
            {
                System.out.println(m + " ");
            }
            System.out.println();
        }

        // int nums[] = new int[4];
        // nums[0] = 4; //make a change to a value
        // nums[1] = 8;
        // nums[2] = 3;
        // nums[3] = 9;

        // int eggs[][] = new int[3][4];

        // for(int j=0;j<3;j++)
        // {
        //     for(int i=0;i<4;i++)
        //     {
        //         eggs[j][i] = (int)(Math.random() * 100);
        //         System.out.println(eggs[j][i]);
        //     }
        // }

        // for(int i=0;i<4;i++)
        // {
        //     System.out.println(nums[i]);
        // }

        // for(int n[]: eggs) //loop over the eggs array
        // {
        //     for(int m: n) // loop over every element in n
        //     {
        //         System.out.println(m + " ");
        //     }
        //     System.out.println();
        // }

    }
}
