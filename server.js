//server.js
var app         = require('express')();
var http        = require('http').Server(app);
var io          = require('socket.io')(http);
var dl          = require('delivery');
var fs          = require('fs');
var formidable  = require('formidable');
var PythonShell = require('python-shell');

var spawn       = require('child_process').spawn;
var stdout  = '';
var stderr  = '';
var index   = 0;
var msg = "";
// supervisor tarafında bir socket açtık..
io.sockets.on('connection', function(socket){
    // web serverı  dinle...
    var delivery = dl.listen(socket);
    // alma işlemi başarılıysa...
    delivery.on('receive.success',function(file){
        msg = "";
        stdout = "";
        fs.writeFile('./receivefiles/' + file.name, file.buffer, function(err){
            if(err){
                console.log('Process_Network_Server => Dosya kaydedilemedi !!! : ' + err);
                io.sockets.emit ('scanResult', "scanError");
            }
            else{
                console.log('Process_Network_Server => ' + file.name + " dosyası başarıyla kaydedildi...");
                
                var command = spawn(process.env.comspec, ['/c', 'C:\\Python27\\python.exe', 'monitoring.py','C:\\Users\\safa\\Desktop\\Github\\Process_Network_Server_Project\\receivefiles\\' + file.name]);
                
                command.stdout.on("data", function(buf) {
                    stdout += buf;
                }); 

                command.on('close', function(code) {
                    console.log(stdout);
                    io.sockets.emit ('processNetworkResult', stdout);
                    
                    fs.unlink('./receivefiles/' + file.name,function(err){
                        console.log("Process_Network_Server => " + file.name + ' dosyası silindi.');
                    });                     
                });
            };
        });
    });	
});

// portu dinle...
http.listen(5001, function () {
  console.log('Process_Network_Server => 5001. port dinleniyor..');
});

