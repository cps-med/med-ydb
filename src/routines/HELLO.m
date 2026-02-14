HELLO ;
  set name="Chuck"
  set db="YottaDB"
  WRITE !
  WRITE " 👋 Hello, ",name,".",?30,"✅ I'm ",db," running on an ARM64 architecture!",!,!
  WRITE " 🤞 This seems to be...",?30,"✅ working."
  WRITE !

  set i=1
  if i=1 do
  . write !,"true"
  . if  write " | true again",!,!

  QUIT