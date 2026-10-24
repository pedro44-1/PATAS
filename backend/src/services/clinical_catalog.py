from sqlalchemy.orm import Session

from src.models.clinical_exam import ClinicalExamFinding, ClinicalExamSystem
from src.models.service_type import ServiceType

DEFAULT_SERVICE_TYPES = (
    ("Consulta", "consulta"),
    ("Banho e tosquia", "banho-tosquia"),
    ("Vacinação", "vacinacao"),
    ("Tratamento", "tratamento"),
    ("Acompanhamento", "acompanhamento"),
    ("Cirurgia", "cirurgia"),
)


DEFAULT_EXAM_CATALOG = {
    "Abdómen": [
        "Sem alteração", "Líquidos", "Massa anormal palpável", "Órgãos inflamados", "Dor à palpação",
        "Ascite", "Timpanismo", "Esplenomegalia", "Hepatomegalia", "Esclerose renal", "Bexiga distendida",
        "Bexiga não palpável", "Linfonodos palpáveis", "Pulso abdominal excessivo", "Hérnia inguinal", "Hérnia umbilical",
    ],
    "Boca, dentes, gengivas": [
        "Dentes em falta", "Dentes partidos", "Gengivites", "Tumores", "Tártaro", "Úlcera / erosão",
        "Prognatismo", "Dentes supranumerários", "Dentes decíduos retidos", "Anodontia", "Coloração",
        "Hipoplasia do esmalte", "Cáries", "Desgaste", "Trauma", "Fístula", "Glândula salivar inflamada",
    ],
    "Coração": [
        "Murmúrios", "Ritmo anormal", "Sopro", "Bradicardia", "Taquicardia", "Fibrilhação", "Sons abafados",
        "III som cardíaco audível", "IV som cardíaco audível", "Área de auscultação aumentada", "Ruído de galope",
        "Maquinaria-like", "Frémito catário",
    ],
    "Gânglios linfáticos": ["Hipertrofiados", "Atrofiados", "Duros", "Moles", "Supurantes", "Punção efetuada"],
    "Membranas mucosas": ["TRC diminuído", "Normais", "Pálidas", "Congestivas", "Cianóticas", "Ictéricas", "Petequiais", "Equimoses", "TRC aumentado"],
    "Músculo esquelético": [
        "Alterações articulares", "Claudicação", "Fracturas", "Alterações falanges", "Displasia da anca",
        "Displasia do cotovelo esquerdo", "Displasia do cotovelo direito", "Sinal de gaveta joelho esquerdo",
        "Sinal de gaveta joelho direito", "Tálus valgus", "Coxa valga", "Coxa vara", "Calvé-Legg-Perthes",
        "Poliartrite", "Osteocondrose", "Osteocondrite dissecante", "Osteossarcoma", "Luxação", "Artrodese", "Pseudo-artrose",
    ],
    "Nariz, garganta": ["Epistaxis", "Espirros", "Descarga nasal", "Gânglios linfáticos hipertrofiados", "Garganta inflamada", "Tosse", "Corpo estranho"],
    "Olhos": [
        "Derrame esclera direita", "Derrame esclera esquerda", "Midríase", "Miose", "Cataratas direita", "Cataratas esquerda",
        "Corrimento direito", "Corrimento esquerdo", "Inflamado direito", "Inflamado esquerdo", "Glândula harder",
        "Úlcera da córnea direita", "Úlcera da córnea esquerda",
    ],
    "Ouvidos": [
        "Ácaros direito", "Ácaros esquerdo", "Otite direita", "Otite esquerda", "Descarga direita", "Descarga esquerda",
        "Alopecia direita", "Alopecia esquerda", "Outros", "Corpo estranho esquerdo", "Corpo estranho direito",
    ],
    "Pele, pêlo": [
        "Equimoses", "Larvas varejeira", "Petéquias", "Alopecias", "Escamas", "Seborreia", "Inflamada / irritada",
        "Nódulos", "Parasitas", "Seca", "Pústulas", "Hiperqueratose", "Hot spot",
    ],
    "Pulmões": ["Asma", "Dispneia", "Sons anormais", "Tosse", "Taquipneia", "Bradipneia", "Estertores", "Crepitações"],
    "Sistema digestivo": ["Diarreia", "Sem alteração", "Vómitos"],
    "Sistema nervoso": ["Convulsões", "Nistagmus", "Ventroflexão da cabeça", "Reflexos aumentados", "Reflexos diminuídos"],
    "Sistema urogenital": ["Tumores mamários", "Corrimento genital", "Criptorquidia unilateral", "Criptorquidia bilateral"],
}


def ensure_clinic_defaults(db: Session, clinic_id: int, *, commit: bool = True) -> None:
    if not db.query(ServiceType).filter(ServiceType.clinic_id == clinic_id).first():
        db.add_all([
            ServiceType(clinic_id=clinic_id, name=name, slug=slug, sort_order=index)
            for index, (name, slug) in enumerate(DEFAULT_SERVICE_TYPES)
        ])

    if not db.query(ClinicalExamSystem).filter(ClinicalExamSystem.clinic_id == clinic_id).first():
        systems = []
        for system_index, (system_name, findings) in enumerate(DEFAULT_EXAM_CATALOG.items()):
            system = ClinicalExamSystem(
                clinic_id=clinic_id,
                name=system_name,
                sort_order=system_index,
                active=1,
            )
            db.add(system)
            db.flush()
            systems.extend(
                ClinicalExamFinding(
                    clinic_id=clinic_id,
                    system_id=system.id,
                    name=finding_name,
                    sort_order=finding_index,
                    active=1,
                )
                for finding_index, finding_name in enumerate(findings)
            )
        db.add_all(systems)

    if commit:
        db.commit()
    else:
        db.flush()
