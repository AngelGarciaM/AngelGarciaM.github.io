// Variables globales
let ronda_perdedores = [];
let ranking_final = [];
let contador_comparaciones = 0;
let seleccionado = 0;
let seleccion_texto = "";
let cierre = 0;
let icancelar = 0;
let tuplas_comparaciones = [];
let diccionario_resultados = [];

async function torneo_recursivo(arr) {
    let ganadores = [];
    let p= []
    // Barajamos los números para simular aleatoriedad
    arr = shuffle(arr);

    while (arr.length > 1) {
        // Emparejamos a los números dos a dos
        let pdf1 = arr.pop();
        let pdf2 = arr.pop();

        if (!containsTuple(tuplas_comparaciones, pdf1.namePdf, pdf2.namePdf)) {
            tuplas_comparaciones.push([pdf1.namePdf, pdf2.namePdf]);
            // Se hace la comparación, mostramos la interfaz
            mostrarArchivos(pdf1, pdf2);

            // Esperamos a que el usuario elija
            await esperarSeleccion();  // Esperar a la selección del usuario
            seleccionado = 0;  // Reseteamos la variable de selección

            // Desplazar la pantalla hacia arriba
            window.scrollTo({
                top: 0,
                behavior: 'smooth' // Animación suave
            });

            if (cierre === 1) {
                // Termina el programa si cierre es 1
                alert("Cerrado");
                return;
            }
            //console.log("Texto Seleccionado: ",seleccion_texto);
            console.log("Tituo: ",pdf1.namePdf);
            console.log("Titulo: ",pdf2.namePdf);
            console.log("Texto Seleccionado: ",seleccion_texto);
            if (seleccion_texto === pdf1.namePdf) {
                contador_comparaciones += 1;
                console.log("Seleccionado: ",pdf1.namePdf);
                ganadores.push(pdf1);
                ronda_perdedores.push(pdf2); // El perdedor va al torneo de perdedores
                let map = new Map()
                let clave = [pdf1.namePdf, pdf2.namePdf].join(',');
                map.set(clave,pdf1.namePdf)
                diccionario_resultados.push(map)
                console.log("Diccionario resultados: ",diccionario_resultados);
                //diccionario_resultados[[pdf1, pdf2]] = pdf1;
            } else if (seleccion_texto=== pdf2.namePdf) {
                contador_comparaciones += 1;
                console.log("Seleccionado: ",pdf2.namePdf);
                ganadores.push(pdf2);
                ronda_perdedores.push(pdf1); // El perdedor va al torneo de perdedores
                let map= new Map()
                let clave = [pdf1.namePdf, pdf2.namePdf].join(',');
                map.set(clave,pdf2.namePdf)
                diccionario_resultados.push(map)
                console.log("Diccionario resultados: ",diccionario_resultados);
                //diccionario_resultados[[pdf1, pdf2]] = pdf2;
            }
            else{
                console.log("El texto seleccionado no coincide con ninguno");
            }
        } else {
            // Si la comparación ya se realizó, usamos el resultado almacenado
            let ganador_comparacion;
            console.log("Se ha repetido una comparacion");
            if (containsKey(diccionario_resultados, pdf1, pdf2)) {
                ganador_comparacion = obtenerResultadoMapa(diccionario_resultados,pdf1,pdf2);
                console.log("Tupla existe, ganador: ", ganador_comparacion);
                if (ganador_comparacion === pdf1.namePdf) {
                    ganadores.push(pdf1);
                    ronda_perdedores.push(pdf2);
                } else if (ganador_comparacion === pdf2.namePdf) {
                    ganadores.push(pdf2);
                    ronda_perdedores.push(pdf1);
                }
            } else if (containsKey(diccionario_resultados, pdf2, pdf1)) {
                ganador_comparacion = obtenerResultadoMapa(diccionario_resultados,pdf2,pdf1);
                console.log("Tupla existe, ganador: ", ganador_comparacion);
                if (ganador_comparacion === pdf1.namePdf) {
                    ganadores.push(pdf1);
                    ronda_perdedores.push(pdf2);
                } else if (ganador_comparacion === pdf2.namePdf) {
                    ganadores.push(pdf2);
                    ronda_perdedores.push(pdf1);
                }
            }else {
                console.log("Fallo aqui");
            }
        }
    }

    if (arr.length === 1) {  // Si hay pdf impares, el último pasa automáticamente
        ganadores.push(arr.pop());
    }

    if (ganadores.length > 1) {
        // Si hay más de un ganador, seguimos con el torneo recursivo
        //console.log("Ganadores de esta ronda:", ganadores);
        console.log("Ganadores: ", ganadores.join(", "));
        await torneo_recursivo(ganadores);  // Continuamos con los ganadores
    } else {
        if (ganadores.length > 0) {
            ranking_final.push(ganadores[0]);
            console.log("Ranking parcial: ", ranking_final.join(", "));
            p = ronda_perdedores.slice();
            ronda_perdedores=[]
            console.log("Perdedores: ", p.join(", "));
            await torneo_recursivo(p);  // Continuamos con los perdedores
        }
    }

    // Mostrar el ranking final en el HTML
    // var vf = document.getElementById("final");
    // vf.innerText = "Ranking Final: " + ranking_final.join(", ");
}

// Función para barajar un arreglo (equivalente a random.shuffle en Python)
function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];  // Intercambio
    }
    return arr;
}

// Función auxiliar para verificar si una tupla está presente en un arreglo
function containsTuple(arr, pdf1, pdf2) {
    let listaBuscada= [pdf1,pdf2];
    let res= arr.some(lista => JSON.stringify(lista) === JSON.stringify(listaBuscada));
    if (!res){
        let listaBuscada= [pdf2,pdf1];
        res= arr.some(lista => JSON.stringify(lista) === JSON.stringify(listaBuscada));
    }
    return res;
}
function containsKey(lista_mapas,pdf1,pdf2){
    let claveABuscar=[pdf1.namePdf,pdf2.namePdf].join(',')
    console.log(`Estoy buscando la clave: ${claveABuscar}`);
    for (let i = 0; i < lista_mapas.length; i++) {
        if (lista_mapas[i].has(claveABuscar)) {
            console.log(`El Map en la posición ${i} tiene la clave: ${claveABuscar}`);
            return true;  // La clave se encontró en uno de los Maps
        }
    }
    console.log("La clave no se encontró en ninguno de los Maps");
    return false;  // La clave no fue encontrada en la lista
}
function obtenerResultadoMapa(lista_mapas,pdf1,pdf2){
    let claveABuscar=[pdf1.namePdf,pdf2.namePdf].join(',')
    for (let i = 0; i < lista_mapas.length; i++) {
        if (lista_mapas[i].has(claveABuscar)) {
            console.log(`La clave ${claveABuscar} se encontró en el Map en la posición ${i}`);
            return lista_mapas[i].get(claveABuscar);  // Devuelve el valor asociado a la clave
        }
    }
    console.log("La clave no se encontró en ninguno de los Maps");
    return false;  // La clave no fue encontrada en la lista

}

// Función simulada para mostrar los archivos (puedes ajustarla a tus necesidades)
function mostrarArchivos(pdf1, pdf2) {
    //Se ponen los dos scrollbar arriba del todo
    scrollToTop("option3");
    scrollToTop("option4");
    // Mostramos en la págin a el título y texto de las dos opciones
    var text_op1 = document.getElementById("option1");
    var title_op1 = document.getElementById("title_option1");
    text_op1.innerText = pdf1.path;
    title_op1.innerText=pdf1.namePdf

    var text_op2 = document.getElementById("option2");
    var title_op2 = document.getElementById("title_option2");
    text_op2.innerText = pdf2.path;
    title_op2.innerText = pdf2.namePdf
}

// Función que devuelve una promesa para esperar la selección del usuario
function esperarSeleccion() {
    return new Promise((resolve) => {
        // Esperamos a que el usuario haga clic en una de las opciones
        document.getElementById("option1").onclick = function() {
            seleccion_texto = document.getElementById("title_option1").innerText;
            seleccionado = 1;
            //document.getElementById("res").innerText = seleccion_texto;
            resolve(seleccion_texto); // Resolvemos la promesa con la opción seleccionada
        };

        document.getElementById("option2").onclick = function() {
            seleccion_texto = document.getElementById("title_option2").innerText;
            seleccionado = 1;
            //document.getElementById("res").innerText = seleccion_texto;
            resolve(seleccion_texto); // Resolvemos la promesa con la opción seleccionada
        };
    });
}
function scrollToTop(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.scrollTop = 0; // Lleva el scroll vertical al inicio
    }
}
function cancelar(){
    // Enviar los datos al servidor
    fetch('/abrir_correcion', {  // Cambiado a '/abrir_correcion'
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Indica que envías datos en formato JSON
        },
        body: JSON.stringify({ cancelar : "cancelar", nombre_correccion: nombre_correcion, lista_titulo: lista_titulo }), // Incluye los datos necesarios
    })
    .then(response => response.json())  // Maneja la respuesta JSON del servidor
    .then(data => {
        console.log("Respuesta del servidor:", data);
        // Aquí puedes redirigir si es necesario o mostrar un mensaje de éxito
        if (data.status === 'cancel') {
            // Redirigir a otra página si es necesario
            window.location.href = "/correcciones"; // O la URL que desees
        }
    });
}


// Llamada inicial para probar el torneo con algunos ejemplos
console.log("Datos recibidos:", pdfData);
console.log("Nombre correccion: ", nombre_correcion)
torneo_recursivo(pdfData).then(() => { //Primero hago el torneo y después envío en ranking final al programa principal

    // Enviar los datos al servidor
    fetch('/abrir_correcion', {  // Cambiado a '/abrir_correcion'
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Indica que envías datos en formato JSON
        },
        body: JSON.stringify({ ranking_final, nombre_correccion: nombre_correcion, lista_titulo: lista_titulo }), // Incluye los datos necesarios
    })
    .then(response => response.json())  // Maneja la respuesta JSON del servidor
    .then(data => {
        console.log("Respuesta del servidor:", data);
        // Aquí puedes redirigir si es necesario o mostrar un mensaje de éxito
        if (data.status === 'success') {
            // Redirigir a otra página si es necesario
            window.location.href = "/correcciones"; // O la URL que desees
        }
    })
});
