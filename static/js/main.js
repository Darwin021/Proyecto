const BtnDelete = document.querySelectorAll('.btn-delete')

if(BtnDelete) {
    const btnArray=Array.from(BtnDelete)
    btnArray.forEach((btn)=> {
        btn.addEventListener('click', (e) => {
            if(!confirm('Estas seguro de querer eliminarlo?'))
                e.preventDefault();
        })
    })
}