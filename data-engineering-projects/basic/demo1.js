function transform(line){
    var values = line.split(',');
    var obj = new Object();
    obj.order_no = values[0];
    obj.item_no = values[1];
    obj.purchased_quantity = values[2];
    var jsonString = JSON.stringify(obj);
    return jsonString;
}