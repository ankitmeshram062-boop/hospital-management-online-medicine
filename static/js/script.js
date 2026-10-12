document.addEventListener("DOMContentLoaded",()=>{
 const date=document.querySelector('input[type="date"]');
 if(date) date.min=new Date().toISOString().split("T")[0];
 document.querySelectorAll(".confirm-delete").forEach(a=>{
   a.addEventListener("click",e=>{
     if(!confirm("Delete this item?")) e.preventDefault();
   });
 });
});
