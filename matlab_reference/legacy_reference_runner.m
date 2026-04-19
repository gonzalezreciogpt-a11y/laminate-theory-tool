function result = legacy_reference_runner(case_data)
% LEGACY_REFERENCE_RUNNER
% Parametric MATLAB wrapper that reproduces the effective behavior of the
% legacy script without modifying the original file.

fiber_types = {
    'RC416T',  62450*1e6, 61200*1e6, 3710*1e6, 0.037, 593, 489.6, 593.3, 489.6, 68.2, 0.43;
    'UD', 130330*1e6, 7220*1e6, 4230*1e6, 0.337, 1433.6, 1003.3, 32.5, 108.3, 76.1, 0.30;
    'Honeycomb', 1.0*1e6, 1.0*1e6, 1.0*1e6, 0.5, 10, 10, 10, 10, 10, 20.0;
    'Dummy', 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001;
};

layers = case_data.layers;
num_capas = length(layers);

fiber_assignment = zeros(1, num_capas);
theta = zeros(1, num_capas);
layer_material_ids = cell(1, num_capas);

for i = 1:num_capas
    material_id = string(layers(i).material_id);
    layer_material_ids{i} = char(material_id);
    fiber_index = find(strcmp(fiber_types(:, 1), material_id), 1);
    if isempty(fiber_index)
        error("Unknown material_id '%s'.", material_id);
    end
    fiber_assignment(i) = fiber_index;
    theta(i) = layers(i).theta_deg;
end

insert_dummy = false;
if isfield(case_data, 'insert_dummy_layer_for_odd_compatibility')
    insert_dummy = logical(case_data.insert_dummy_layer_for_odd_compatibility);
end

if insert_dummy && mod(num_capas, 2) == 1
    fiber_assignment(end + 1) = find(strcmp(fiber_types(:, 1), 'Dummy'), 1);
    theta(end + 1) = 0;
    layer_material_ids{end + 1} = 'Dummy'; %#ok<AGROW>
    num_capas = length(fiber_assignment);
end

es_simetrico = logical(case_data.is_symmetric);

core_material_name = 'Honeycomb';
if isfield(case_data, 'core_material_id')
    core_material_name = char(string(case_data.core_material_id));
end
capa_central = fiber_types{strcmp(fiber_types(:,1), core_material_name), 11};

z = zeros(num_capas + 1, 1);
espesor_total = 0;
for i = 1:num_capas
    fiber_index = fiber_assignment(i);
    h = fiber_types{fiber_index, 11};
    espesor_total = espesor_total + h;
end

if es_simetrico
    mitad_thickness = espesor_total / 2;
    acumulado_thickness = 0;

    for i = 1:ceil(num_capas / 2)
        fiber_index = fiber_assignment(i);
        h = fiber_types{fiber_index, 11};
        acumulado_thickness = acumulado_thickness + h;
        z(i) = mitad_thickness - acumulado_thickness + h / 2;
    end

    if mod(num_capas, 2) == 1
        capa_central = ceil(num_capas / 2) + 1;
        h_central = fiber_types{fiber_assignment(capa_central), 11};
        z(capa_central) = mitad_thickness - acumulado_thickness - h_central / 2;
        acumulado_thickness = acumulado_thickness + h_central;
    end

    for i = ceil(num_capas / 2) + 1:num_capas
        z(i) = -z(num_capas + 1 - i);
    end

    z(num_capas + 1) = -mitad_thickness;
else
    acumulado_thickness = 0;
    for i = 1:num_capas
        fiber_index = fiber_assignment(i);
        h = fiber_types{fiber_index, 11};
        acumulado_thickness = acumulado_thickness + h;
        z(i) = acumulado_thickness - h / 2 - espesor_total / 2;
    end

    z(num_capas + 1) = -espesor_total / 2;
end

A = zeros(3, 3);
B = zeros(3, 3);
D = zeros(3, 3);

last_nu12 = 0;
for i = 1:num_capas
    fiber_index = fiber_assignment(i);
    E1 = fiber_types{fiber_index, 2};
    E2 = fiber_types{fiber_index, 3};
    G12 = fiber_types{fiber_index, 4};
    nu21 = fiber_types{fiber_index, 5};
    h = fiber_types{fiber_index, 11};

    nu12 = (E2 / E1) * nu21;
    last_nu12 = nu12;

    Q11 = E1 / (1 - nu12 * nu21);
    Q12 = (nu21 * E2) / (1 - nu12 * nu21);
    Q22 = E2 / (1 - nu12 * nu21);
    QSS = G12;

    m = cosd(theta(i));
    n = sind(theta(i));

    Qxx = Q11 * (m^4) + 2 * (Q12 + 2 * QSS) * (n^2) * (m^2) + Q22 * (n^4);
    Qyx = (Q11 + Q22 - 4 * QSS) * (n^2) * (m^2) + Q12 * (n^4 + m^4);
    Qyy = Q11 * (n^4) + 2 * (Q12 + 2 * QSS) * (n^2) * (m^2) + Q22 * (m^4);
    Qxs = (Q11 - Q12 - 2 * QSS) * n * (m^3) + (Q12 - Q22 + 2 * QSS) * n * (m^3);
    Qys = (Q11 - Q12 - 2 * QSS) * m * (n^3) + (Q12 - Q22 + 2 * QSS) * m * (n^3);
    Qss = (Q11 + Q22 - 2 * Q12 - 2 * QSS) * (n^2) * (m^2) + QSS * (n^4 + m^4);

    QXY = [Qxx, Qyx, Qxs; Qyx, Qyy, Qys; Qxs, Qys, Qss];
    A = A + QXY * h;
    B = B + QXY * (z(i)^2 - z(i+1)^2) / 2.0;
    D = D + QXY * ((z(i)^3 - z(i+1)^3) / 3);
end

A1 = A / (espesor_total);
a = inv(A1);
D1 = D / (espesor_total);
d = inv(D1);

E11 = 1 / a(1, 1);
E22 = 1 / a(2, 2);
G122 = 1 / a(3, 3);
nuu21 = -a(2, 1) / a(1, 1);
nuu12 = -a(1, 2) / a(2, 2);
G12G = E11 / (2 * (1 + last_nu12));

defaults.elastic_gradient = 2649;
defaults.rigidez_rig = 14871;
defaults.span_m = 0.400;
defaults.span_mm = 400;
defaults.width_m = 0.275;
defaults.width_mm = 275;

if isfield(case_data, 'three_point_bending')
    bending = case_data.three_point_bending;
    bending_fields = fieldnames(defaults);
    for i = 1:length(bending_fields)
        field_name = bending_fields{i};
        if isfield(bending, field_name)
            defaults.(field_name) = bending.(field_name);
        end
    end
end

E1_P_Manual = 1 / a(1, 1);
th_Fibra = espesor_total;
Elastic_Gradient_Corregido = (defaults.elastic_gradient * defaults.rigidez_rig) / (defaults.rigidez_rig - defaults.elastic_gradient);
EI_ensayo = Elastic_Gradient_Corregido * 1000 * defaults.span_m^3 / 48;
E_fibra_ensayo = defaults.span_mm^3 / (24 * defaults.width_mm * th_Fibra * (th_Fibra + capa_central)^2) * Elastic_Gradient_Corregido;
EI_theory = 0.5 * (E1_P_Manual * defaults.width_m * (th_Fibra * 0.001) * (th_Fibra * 0.001 + capa_central * 0.001)^2);
Elastic_gradient_Theory = 48 * EI_theory / (defaults.span_m^3 * 1000);

result = struct();
result.fiber_assignment = fiber_assignment;
result.material_ids = {layer_material_ids{:}};
result.theta = theta;
result.es_simetrico = es_simetrico;
result.espesor_total = espesor_total;
result.z = z;
result.A = A;
result.B = B;
result.D = D;
result.A1 = A1;
result.D1 = D1;
result.E11 = E11;
result.E22 = E22;
result.G122 = G122;
result.nuu12 = nuu12;
result.nuu21 = nuu21;
result.last_nu12 = last_nu12;
result.G12G = G12G;
result.E1_P_Manual = E1_P_Manual;
result.th_Fibra = th_Fibra;
result.Elastic_Gradient_Corregido = Elastic_Gradient_Corregido;
result.EI_ensayo = EI_ensayo;
result.E_fibra_ensayo = E_fibra_ensayo;
result.EI_theory = EI_theory;
result.Elastic_gradient_Theory = Elastic_gradient_Theory;
result.legacy_capa_central_value = capa_central;
end
