#! /usr/bin/env python3

import os, sys, re

#gets the process ID 
pid = os.getpid()

while 1:
    #write to the terminal
    os.write(1,("$").encode())
    #reads user input
    cmd = os.read(0, 100).decode().strip()
    #split user input 
    args = cmd.split(" ")
    #piped --> incase we recieve more than 1 command
    piped = False
    args2 = []

    #command is empty 
    if(len(cmd)==0):
        pass
    elif(args[0] == "exit"):
        break
    #change directory
    elif(args[0]=="cd"):
        os.chdir(args[1])
    else:
        #checkoing user input
        for i in range(len(args)-1):
            #checking for more piping commad1 | command2 
            if(args[i]=="|"):
                piped = True
                n = len(args)
                #grab the input after pipping symbol 
                for j in range(0, n-i):
                    #add contents to a second list
                    args2.append(args.pop())
                args2.pop()
                args2.reverse()
                #file descriptors to pipe read and  pipe write(writing)
                pr,pw = os.pipe() #channel created so both pipes interact
                for f in (pr, pw):
                    os.set_inheritable(f, True)#allowing first commands input to be second commands output
                break
        
        #os.fork() returns a different value depending on wether is the parent process or the child process 
        rc = os.fork()#27 ..... rc holds the value of  whatever os.fork() return s
        #parent process > 0 
        #child process == 0

        #error occured
        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)

        #child 1--> executes command provided by the user
        elif rc == 0: 
            if(piped):
                os.close(1)   # redirect child's stdout
                os.dup(pw)
                for fd in (pr, pw):
                    os.close(fd) #close stdout to send to pipe
                os.set_inheritable(1, True)#place holder for executing command
            else: 
                for i in range(len(args)-1):
                    if(args[i]==">"): #output redirection
                        os.close(1)
                        fa = str(os.open(args[i+1], os.O_WRONLY | os.O_CREAT))
                        os.set_inheritable(1, True)
                        n = len(args)
                        for j in range(0, n-i):
                            args.pop()
                        break

            for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                program = "%s/%s" % (dir, args[0])
                try:
                    #looks for rm or any other commands the user may have passed
                    #if the 'Program is found then my shell successfully executes the command/ external program 
                    os.execve(program, args, os.environ)
                except FileNotFoundError:             
                    pass                             
            os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
            sys.exit(1)                 # terminate with error


        #waits for user input on the shell promt $
        else:  

            if(piped):
                rc2 = os.fork()
                if rc2 < 0:
                    os.write(2, ("fork failed, returning %d\n" % rc).encode())
                    sys.exit(1)

                elif rc2 == 0: #Child 2
                    os.close(0)# close stdinput to read from pipe only
                    os.dup(pr)
                    for fd in (pw, pr):
                        os.close(fd)
                    os.set_inheritable(0, True)
                    for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                        program = "%s/%s" % (dir, args2[0])
                        try:
                            os.execve(program, args2, os.environ) # try to exec program
                        except FileNotFoundError:             # expected
                            pass                              # fail quietly
                    os.write(2, ("Child2:    Could not exec %s\n" % args2[0]).encode())
                    sys.exit(1)
                else:
                    if(not cmd[len(cmd)-1]=="$"):
                        childPid2Code = os.wait()

            elif(not cmd[len(cmd)-1]=="$"):
                childPidCode = os.wait()