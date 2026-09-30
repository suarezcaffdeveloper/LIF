/*
 * Configuración de la landing de ElTablón.
 *
 * ⚠️  TODOS ESTOS VALORES SON DE EJEMPLO. Reemplazalos por los reales antes de publicar.
 *     Mientras EJEMPLO sea true, la consola del navegador avisa que faltan datos.
 */
window.ELTABLON = {
  EJEMPLO: true,

  // WhatsApp: número completo con código de país, sin "+" ni espacios (Argentina: 549 + área + número).
  WHATSAPP: "5493468522516",
  WHATSAPP_MENSAJE: "Hola! Vi ElTablón y quiero conocer el sistema para mi liga.",

  // Email de contacto.
  EMAIL: "suarezz.santi01@gmail.com",

  // Formulario: URL de un servicio que reciba los datos (por ejemplo Formspree: "https://formspree.io/f/xxxxxxx").
  // Si queda vacío, el formulario abre el programa de correo del visitante con el mensaje ya escrito.
  FORM_ENDPOINT: "https://formsubmit.co/ajax/suarezz.santi01@gmail.com",

  // Demo en vivo: dirección donde publiques la instancia con LIGA=demo y DEMO_TEMAS=1.
  // Con DEMO_EN_VIVO en false, la landing muestra capturas en lugar de incrustar el sitio.
  DEMO_URL: "https://demo.eltablon.example",
  DEMO_EN_VIVO: false
};

if (window.ELTABLON.EJEMPLO) {
  console.warn("[ElTablón] La landing usa datos de contacto de ejemplo. Editá landing/js/config.js antes de publicar.");
}
