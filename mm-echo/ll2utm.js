// Stałe i parametry elipsoidy (WGS84)
const PI = 3.14159265358979;
const A = 6378137; 
const B = 6356752.314; 
const UTM_SCALE_FACTOR = 0.9996;

function degToRad(deg) {
    return (deg / 180) * PI;
}

function radToDeg(rad) {
    return (rad / PI) * 180;
}

function utmCentralMeridian(zone) {
    return degToRad(-183 + (zone * 6));
}

function ll2utm(lat, lon) { // Lat/Lon -> UTM (X, Y, Zone)
    return latLonToUTMXY(degToRad(lat), degToRad(lon));
}

function utm2ll(x, y, zone, southhemi) { // UTM -> Lat/Lon
    const ll = utmXYToLatLon(x, y, zone, southhemi);
    ll[0] *= 180 / PI;
    ll[1] *= 180 / PI;
    return ll; // Zwraca tablicę [Latitude, Longitude]
}

function arcLengthOfMeridian(phi) {
    const n = (A - B) / (A + B);
    const alpha = ((A + B) / 2) * (1 + (n * n) / 4 + (n * n * n * n) / 64);
    const beta = -3 * n / 2 + 9 * (n * n * n) / 16 - 3 * (n * n * n * n * n) / 32;
    const gamma = 15 * (n * n) / 16 - 15 * (n * n * n * n) / 32;
    const delta = -35 * (n * n * n) / 48 + 105 * (n * n * n * n * n) / 256;
    const epsilon = 315 * (n * n * n * n) / 512;    
    return alpha * (phi + (beta * Math.sin(2 * phi)) + (gamma * Math.sin(4 * phi)) + (delta * Math.sin(6 * phi)) + (epsilon * Math.sin(8 * phi)));
}

function footpointLatitude(y) {
    const n = (A - B) / (A + B);
    const alpha = ((A + B) / 2) * (1 + (n * n / 4) + (n * n * n * n / 64)); 
    y /= alpha;    
    const beta = 3 * n / 2 - 27 * (n * n * n) / 32 + 269 * (n * n * n * n * n) / 512;
    const gamma = 21 * (n * n) / 16 - 55 * (n * n * n * n) / 32;
    const delta = 151 * (n * n * n) / 96 - 417 * (n * n * n * n * n) / 128;
    const epsilon = 1097 * (n * n * n * n) / 512;    
    return y + beta * Math.sin(2 * y) + gamma * Math.sin(4 * y) + delta * Math.sin(6 * y) + epsilon * Math.sin(8 * y); 
}

function mapLatLonToXY(phi, lambda, lambda0) {
    const {cos, sin, pow, sqrt} = Math;
    const ep2 = (A * A - B * B) / (B * B);
    const nu2 = ep2 * pow(cos(phi), 2);
    const n = (A * A) / (B * sqrt(1 + nu2));
    const t = sin(phi) / cos(phi);
    const t2 = t * t;
    const l = lambda - lambda0;    
    const l3 = 1 - t2 + nu2;
    const l4 = 5 - t2 + 9 * nu2 + 4 * (nu2 * nu2);
    const l5 = 5 - 18 * t2 + (t2 * t2) + 14 * nu2 - 58 * t2 * nu2;
    const l6 = 61 - 58 * t2 + (t2 * t2) + 270 * nu2 - 330 * t2 * nu2;
    const l7 = 61 - 479 * t2 + 179 * (t2 * t2) - (t2 * t2 * t2);
    const l8 = 1385 - 3111 * t2 + 543 * (t2 * t2) - (t2 * t2 * t2);
    const xy = [];
    /* easting (x) */
    xy[0] = n * cos(phi) * l + (n / 6 * pow(cos(phi), 3) * l3 * pow(l, 3))
        + (n / 120 * pow(cos(phi), 5) * l5 * pow(l, 5)) + (n / 5040 * pow(cos(phi), 7) * l7 * pow(l, 7));
    /* northing (y) */
    xy[1] = arcLengthOfMeridian(phi)
        + (t / 2 * n * pow(cos(phi), 2) * pow(l, 2)) + (t / 24 * n * pow(cos(phi), 4) * l4 * pow(l, 4))
        + (t / 720 * n * pow(cos(phi), 6) * l6 * pow(l, 6)) + (t / 40320 * n * pow(cos(phi), 8) * l8 * pow(l, 8));        
    return xy;
}

function mapXYToLatLon(x, y, lambda0) {
    const {cos, sin, pow, sqrt} = Math;
    const phif = footpointLatitude(y);
    const ep2 = (Math.pow(A, 2) - Math.pow(B, 2)) / Math.pow(B, 2);
    const cf = Math.cos(phif);
    const nuf2 = ep2 * Math.pow(cf, 2);
    const Nf = Math.pow(A, 2) / (B * Math.sqrt(1 + nuf2));
    let Nfpow = Nf;
    const tf = Math.sin(phif) / Math.cos(phif);
    const tf2 = tf * tf;
    const tf4 = tf2 * tf2;   
    const x1frac = 1 / (Nfpow * cf);
    Nfpow *= Nf; const x2frac = tf / (2 * Nfpow);
    Nfpow *= Nf; const x3frac = 1 / (6 * Nfpow * cf);
    Nfpow *= Nf; const x4frac = tf / (24 * Nfpow);
    Nfpow *= Nf; const x5frac = 1 / (120 * Nfpow * cf);
    Nfpow *= Nf; const x6frac = tf / (720 * Nfpow);
    Nfpow *= Nf; const x7frac = 1 / (5040 * Nfpow * cf);
    Nfpow *= Nf; const x8frac = tf / (40320 * Nfpow);    
    const x2poly = -1 - nuf2;
    const x3poly = -1 - 2 * tf2 - nuf2;
    const x4poly = 5 + 3 * tf2 + 6 * nuf2 - 6 * tf2 * nuf2 - 3 * (nuf2 * nuf2) - 9 * tf2 * (nuf2 * nuf2); 
    const x5poly = 5 + 28 * tf2 + 24 * tf4 + 6 * nuf2 + 8 * tf2 * nuf2;
    const x6poly = -61 - 90 * tf2 - 45 * tf4 - 107 * nuf2 + 162 * tf2 * nuf2;
    const x7poly = -61 - 662 * tf2 - 1320 * tf4 - 720 * (tf4 * tf2);
    const x8poly = 1385 + 3633 * tf2 + 4095 * tf4 + 1575 * (tf4 * tf2);
    const philambda = [];
    /* Calculate latitude */
    philambda[0] = phif + x2frac * x2poly * x * x + x4frac * x4poly * pow(x, 4)
        + x6frac * x6poly * pow(x, 6) + x8frac * x8poly * pow(x, 8);    
    /* Calculate longitude */
    philambda[1] = lambda0 + x1frac * x + x3frac * x3poly * pow(x, 3)
        + x5frac * x5poly * pow(x, 5) + x7frac * x7poly * pow(x, 7);    
    return philambda;
}

function latLonToUTMXY(lat, lon) {
    const zone = Math.floor((lon * 180 / PI + 180) / 6) + 1; 
    const xy = mapLatLonToXY(lat, lon, utmCentralMeridian(zone));
    let southhemi = false;
    xy[0] = xy[0] * UTM_SCALE_FACTOR + 500000;
    xy[1] *= UTM_SCALE_FACTOR;
    if (xy[1] < 0) { xy[1] += 10000000; southhemi = true;}
    xy[2] = zone;
    xy[3] = southhemi;
    return xy; // Zwraca [X, Y, Zone, southhemi]
}

function utmXYToLatLon(x, y, zone, southhemi) {
    x -= 500000; 
    x /= UTM_SCALE_FACTOR;
    if (southhemi) { y -= 10000000; } 
    y /= UTM_SCALE_FACTOR;    
    return mapXYToLatLon(x, y, utmCentralMeridian(zone));    
}

/*
console.log("ll2utm.js:");
const [utmX, utmY, zone, southhemi] = ll2utm(54, 18);
const [lat, lon] = ll2utm(utmX, utmY, zone, southhemi);
console.log(`X: ${utmX}, Y: ${utmY}, Strefa: ${zone}`);
console.log(`Lat: ${lat}, Lon: ${lon}`);
*/