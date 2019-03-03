var mongoose = require('mongoose');

mongoose.Promise = require('bluebird');

var mongoDB = 'mongodb://192.168.175.148:27017/BlackListDB';

mongoose.connect(mongoDB,function(err,err){
    if(err){
        console.log('mongoose error: '+ err);
    }
    else{
        console.log('mongoose connected : ' + mongoDB);
    }
});