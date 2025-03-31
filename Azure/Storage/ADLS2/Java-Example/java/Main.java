public class Main {
    public static void main(String[] args) {
        String storageAccountName = args[0];
        String storageContainer = args[1];
        String storageAccessKey = args[2];

        API api = new API(storageAccountName, storageContainer, storageAccessKey);

        // Create a CSV file automatically on the ADLS Gen 2 filesystem called test.csv
        String csv = "test1,test2\n1,2\n3,4";
        api.createFile("/test.csv");
        api.appendDataToFile("/test.csv", 0, csv.getBytes());
        api.flushDataToFile("/test.csv", csv.getBytes().length);
    }
}
