class Calculator{

    public int add(int n1,int n2){

        int r = n1 + n2;
        return r;
    }

    public int sub(int n3, int n4){
        int r2 = n4 - n3;
        return r2;
    }
}

public class OOP { 
    public static void main(String[] args) {
        
        int num1 = 4;
        int num2 = 5;

        Calculator calc = new Calculator(); //Create the object

        int result = calc.add(num1,num2);
        int result2 = calc.sub(num2, num1);

        System.out.println(result + " " + result2);
    }
}
