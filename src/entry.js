var AmazonCognitoIdentity = require('amazon-cognito-identity-js');
var AWS = require('aws-sdk');

function uploadFile(fileName, fileContent) {
    var poolData = {
        UserPoolId : 'us-east-1_noGkk04sC', // Your user pool id here
        ClientId : '2bo2g45f23039mjhqjt0p18d79' // Your client id here
    };
    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

    // Here we will retrieve the current session, if a user is logged in
    var cognitoUser = userPool.getCurrentUser();

    if (cognitoUser != null) {
        cognitoUser.getSession(function(err, session) {
            if (err) {
                alert(err);
                return;
            }
            AWS.config.credentials = new AWS.CognitoIdentityCredentials({
                IdentityPoolId : 'us-east-1:caa20059-c2bd-416c-94c1-43988c2e10e3', // Your identity pool id here
                Logins : {
                    // change the URL below to the correct region
                    'cognito-idp.us-east-1.amazonaws.com/us-east-1_noGkk04sC' : session.getIdToken().getJwtToken()
                }
            });

            // Instantiate aws sdk service objects now that the credentials have been updated.
            var s3 = new AWS.S3({
                apiVersion: '2006-03-01',
                params: {Bucket: 'assigment2-group6-bucket/images'} // Replace with your S3 bucket name
            });

            s3.upload({Key: fileName, Body: fileContent}, function(err, data) {
                if (err) {
                    console.log(err, 'There was an error uploading your file');
                } else {
                    console.log('Successfully uploaded file.');
                }
            });
        });
    } else {
        console.log('User not logged in');
    }
}

// We expose the uploadFile function globally so it can be called from the HTML
window.uploadFile = uploadFile;
