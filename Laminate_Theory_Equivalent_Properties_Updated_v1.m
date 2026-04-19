clc
clear variables

% Definir tipos de fibras y sus propiedades en una tabla
% {Nombre, E1 (Pa), E2 (Pa), G12 (Pa), nu12, X, X_, Y, Y_, S, espesor (mm)}
%  X, X_, Y, Y_, S no se usan para el código, no es necesario ponerlo
fiber_types = {
    'RC416T',  62450*1e6, 61200*1e6, 3710*1e6, 0.037, 593, 489.6, 593.3, 489.6, 68.2, 0.43; %Twill
    'UD', 130330*1e6, 7220*1e6, 4230*1e6, 0.337, 1433.6, 1003.3, 32.5, 108.3, 76.1, 0.30; %Unidireccional
    'Honeycomb', 1.0*1e6, 1.0*1e6, 1.0*1e6, 0.5, 10, 10, 10, 10, 10, 20.0; % Core honeycomb como ejemplo
   'Dummy', 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001; %poner cuando el número de capas es impar
};

% Número de capas del laminado

% Asignar tipos de fibra a cada capa (índices que corresponden a la tabla 'fiber_types')
fiber_assignment = [1,2,1,4];  % Aquí 3 representa la capa central de honeycomb
num_capas = length(fiber_assignment);  % Puede ser modificado para definir cuántas capas
capa_central = fiber_types{strcmp(fiber_types(:,1),'Honeycomb'), 11}; % Espesor del core en mm
% Orientaciones de cada capa (en grados)
theta = [45, 0, 90, 0]; % Añadimos orientación ficticia al core para que 
% el código corra sin problema (no afecta porque no tiene orientación en la realidad)

% Opción para seleccionar si el laminado será simétrico
es_simetrico = true;  % Cambia a `false` si no es simétrico y a 'true' si es simétrico

% Inicializar las posiciones z de las capas
z = zeros(num_capas + 1, 1);
total_thickness = 0;  % Mantener la suma de los espesores

% Calcular el espesor total del laminado
espesor_total = 0;
for i = 1:num_capas
    fiber_index = fiber_assignment(i);  % Obtener el índice de la fibra
    h = fiber_types{fiber_index, 11};   % Espesor de la fibra seleccionada
    espesor_total = espesor_total + h;  % Sumar el espesor de la capa
end

% Cálculo de posiciones de las capas teniendo en cuenta si es simétrico
if es_simetrico
    % Inicializar la posición inicial y la mitad del espesor total
    mitad_thickness = espesor_total / 2;  % La mitad del espesor total ya calculado
    acumulado_thickness = 0;  % Variable para acumular el espesor de cada capa

    % Cálculo solo para la mitad superior (hasta la capa central)
    for i = 1:ceil(num_capas / 2)
        fiber_index = fiber_assignment(i);   % Obtener el índice de la fibra para esta capa
        h = fiber_types{fiber_index, 11};    % Obtener el espesor de la capa seleccionada

        acumulado_thickness = acumulado_thickness + h;  % Sumar el espesor de la capa a la acumulación
        z(i) = mitad_thickness - acumulado_thickness + h / 2;  % Posición del centro de la capa desde el centro del laminado
    end

    % Añadir la capa central si hay un número impar de capas
    if mod(num_capas, 2) == 1
        capa_central = ceil(num_capas / 2) + 1;
        h_central = fiber_types{fiber_assignment(capa_central), 11};
        z(capa_central) = mitad_thickness - acumulado_thickness - h_central / 2;  % Posición del centro de la capa central
        acumulado_thickness = acumulado_thickness + h_central;  % Sumar el espesor de la capa central
    end

    % Reflejar las capas inferiores de forma simétrica
    for i = ceil(num_capas / 2) + 1:num_capas
        z(i) = -z(num_capas + 1 - i);  % Reflejar las posiciones simétricas
    end

    % Ajustar el último valor de z para que coincida con el límite inferior
    z(num_capas + 1) = -mitad_thickness;
else
    % Laminado no simétrico: se calculan las posiciones normalmente
    acumulado_thickness = 0;  % Resetear el espesor acumulado para este caso
    for i = 1:num_capas
        fiber_index = fiber_assignment(i);  % Obtener el índice de la fibra
        h = fiber_types{fiber_index, 11};   % Espesor de la fibra seleccionada

        acumulado_thickness = acumulado_thickness + h;  % Sumar el espesor de la capa
        z(i) = acumulado_thickness - h / 2 - espesor_total / 2;  % Posición del centro de la capa desde el fondo centrado
    end

    % Ajustar el último valor de z para que coincida con el límite inferior
    z(num_capas + 1) = -espesor_total / 2;
end

% Mostrar el espesor total del laminado
disp(['El espesor total del laminado es: ', num2str(espesor_total), ' mm']);

% Mostrar si es simétrico o no en los resultados
if es_simetrico
    disp('El laminado es simétrico.');
else
    disp('El laminado NO es simétrico.');
end


% Matrices de rigidez globales y locales inicializadas
A = zeros(3, 3);  % Matriz A
B = zeros(3, 3);  % Matriz B, aunque sea simétrico, se calcula por completitud
D = zeros(3, 3);  % Matriz D
AA= zeros(3,3)
% Inicialización de variables para ángulos y componentes de rigidez
m = zeros(size(theta));
n = zeros(size(theta));

Qxx = zeros(size(theta));
Qyx = zeros(size(theta));
Qyy = zeros(size(theta));
Qxs = zeros(size(theta));
Qys = zeros(size(theta));
Qss = zeros(size(theta));
QXY = cell(size(theta));  % Celda para almacenar las matrices de rigidez de cada capa

% Bucle para calcular las propiedades de cada capa
for i = 1:num_capas
    % Seleccionar el tipo de fibra para esta capa
    fiber_index = fiber_assignment(i);
    E1 = fiber_types{fiber_index, 2};    % Módulo de elasticidad en la dirección 1
    E2 = fiber_types{fiber_index, 3};    % Módulo de elasticidad en la dirección 2
    G12 = fiber_types{fiber_index, 4};   % Módulo de corte
    nu21 = fiber_types{fiber_index, 5};  % Coeficiente de Poisson
    h = fiber_types{fiber_index, 11};    % Espesor de la capa basada en la fibra
    
    % Calcular nu12 a partir de E1, E2 y nu21
    nu12 = (E2 / E1) * nu21;

    % Matriz de rigidez en coordenadas locales (Q)
    Q11 = E1 / (1 - nu12 * nu21);
    Q12 = (nu21 * E2) / (1 - nu12 * nu21);
    Q21 = Q12;
    Q22 = E2 / (1 - nu12 * nu21);
    QSS = G12;

    % Conversión a coordenadas globales usando el ángulo theta (m = coseno, n = seno)
    m(i) = cosd(theta(i));
    n(i) = sind(theta(i));
    
    % Cálculo de los términos de la matriz de rigidez global
    Qxx(i) = Q11 * (m(i)^4) + 2 * (Q12 + 2 * QSS) * (n(i)^2) * (m(i)^2) + Q22 * (n(i)^4);
    Qyx(i) = (Q11 + Q22 - 4 * QSS) * (n(i)^2) * (m(i)^2) + Q12 * (n(i)^4 + m(i)^4);
    Qyy(i) = Q11 * (n(i)^4) + 2 * (Q12 + 2 * QSS) * (n(i)^2) * (m(i)^2) + Q22 * (m(i)^4);
    Qxs(i) = (Q11 - Q12 - 2 * QSS) * n(i) * (m(i)^3) + (Q12 - Q22 + 2 * QSS) * n(i) * (m(i)^3);
    Qys(i) = (Q11 - Q12 - 2 * QSS) * m(i) * (n(i)^3) + (Q12 - Q22 + 2 * QSS) * m(i) * (n(i)^3);
    Qss(i) = (Q11 + Q22 - 2 * Q12 - 2 * QSS) * (n(i)^2) * (m(i)^2) + QSS * (n(i)^4 + m(i)^4);
    
    % Guardar la matriz de rigidez de esta capa
    QXY{i} = [Qxx(i), Qyx(i), Qxs(i); Qyx(i), Qyy(i), Qys(i); Qxs(i), Qys(i), Qss(i)];
    
    % Sumar los términos a las matrices A, B y D
    A = A + QXY{i} * h;
    
    B = B + QXY{i} * (z(i)^2 - z(i+1)^2) / 2.0;
    D = D + QXY{i} * ((z(i)^3 - z(i+1)^3) / 3);
end



% Calcular las propiedades equivalentes del laminado (matriz A)
A1 = A / (espesor_total);  % Dividir por el espesor total del laminado
a = inv(A1);  % Invertir la matriz A1 para obtener los términos de las propiedades del laminado
D1 = D / (espesor_total);
d=inv(D1);
% Propiedades finales del laminado
E11 = 1 / a(1, 1);  % Módulo de elasticidad en la dirección 1 (longitudinal)
E22 = 1 / a(2, 2);  % Módulo de elasticidad en la dirección 2 (transversal)
G122 = 1 / a(3, 3); % Módulo de corte en el plano 1-2
E111=1/d(1,1);
nuu21 = -a(2, 1) / a(1, 1);  % Coeficiente de Poisson en la dirección 2->1
nuu12 = -a(1, 2) / a(2, 2);  % Coeficiente de Poisson en la dirección 1->2

% Cálculo del módulo de corte global basado en E11 y nu12
G12G = E11 / (2 * (1 + nu12));  % Usando la relación clásica entre módulo de elasticidad y módulo de corte

% Mostrar resultados
disp('Propiedades del laminado sin contar al nucleo:')  % Imprimir resultados

% E11: Módulo de elasticidad en la dirección 1 (dirección longitudinal del laminado)
disp(['E11: ', num2str(E11 / 1e9), ' GPa']);  

% E22: Módulo de elasticidad en la dirección 2 (dirección transversal al laminado)
disp(['E22: ', num2str(E22 / 1e9), ' GPa']);  

% G12: Módulo de corte, que describe la rigidez al corte en el plano 1-2
disp(['G12: ', num2str(G122 / 1e9), ' GPa']);  

% nu12: Coeficiente de Poisson, indica cómo una deformación en la dirección 1 causa deformación en la dirección 2
disp(['nu12: ', num2str(nuu12)]);  

% nu21: Coeficiente de Poisson inverso, indica cómo una deformación en la dirección 2 causa deformación en la dirección 1
disp(['nu21: ', num2str(nuu21)]);  

% G12G: Módulo de corte global, calculado a partir de E11 y nu12, también describe la rigidez al corte
disp(['G12G: ', num2str(G12G / 1e9), ' GPa']);



%constante Ingenieria: E1 de la lamina en el plano
E1_P_Manual=1/a(1,1)
%E1_P_Manual=79.1e3;%calculado con la teoria del laminado usando unicamente la fibra

%Aplicamos la formula para conseguir E flexion del Laminado
th_Fibra=(espesor_total)

% Calculos relacionados con el dato conocido de la rigidez en el ensayo
Elastic_gradient=2649      % Este valor cogido del excel pendiente F vs D, (Actualizar)
Rigidez_Rig= 14871         %Valor teorico obtenido (no tocar)
Elastic_Gradient_Corregido= (Elastic_gradient*Rigidez_Rig)/(Rigidez_Rig-Elastic_gradient)
EI_ensayo=Elastic_Gradient_Corregido*1000*0.400^3/48

E_fibra_ensayo=400^3/(24*(275)*(th_Fibra)*(th_Fibra+capa_central)^2)*Elastic_Gradient_Corregido



%Teoria de Laminados (Calculo Teorico del Matlab de Propiedades)
EI_theory=0.5*(E1_P_Manual*(0.275)*(th_Fibra*0.001)*(th_Fibra*0.001+capa_central*0.001)^2)
Elastic_gradient_Theory=48*EI_theory/(0.400^3*1000)

