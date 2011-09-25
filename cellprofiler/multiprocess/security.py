'''
Created on Sep 25, 2011

@author: jacob
'''
import hashlib

#Requires pycrypto
from Crypto.PublicKey import RSA
from Crypto import Random

def create_signature(key, message):
    if(type(key) is str):
        #Assume string is path load from file
        key = get_key(key)
    hash_val = hashlib.sha1(message).hexdigest()
    #Second paramater not used in RSA
    signature = key.sign(hash_val, '')
    return signature, key.publickey().exportKey()

def get_key(file_path):
    infile = open(file_path, 'r')
    keydata = infile.read()
    key = RSA.importKey(keydata)
    infile.close()
    return key

def verify_message(message):
    key = RSA.importKey(message['public_key'])
    signature = message['signature']
    data = message['data']
    data_hash = hashlib.sha1(data).hexdigest()
    return key.verify(data_hash, signature)

def generate_keypair(outpublic, outprivate, keylength=2048):
    rng = Random.new().read
    #Note: This takes about 10 seconds on my slow machine
    RSAkey = RSA.generate(keylength, rng)
    objs = [RSAkey.publickey(), RSAkey]
    for ind, path in enumerate([outpublic, outprivate]):
        outfi = open(path, 'w')
        data = objs[ind].exportKey()
        outfi.write(data)
        outfi.close()

#if __name__ == "__main__":
#    import os
#    cur_dir = os.path.dirname(os.path.abspath(__file__))
#    outdir = os.path.join(cur_dir,'tests','data')
#    outpri = os.path.join(outdir,'test_rsa')
#    outpub = os.path.join(outdir,'test_rsa.pub')
#    generate_keypair(outpub,outpri)
