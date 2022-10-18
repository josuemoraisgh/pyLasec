from talk_in_code import pt_translator
import pytest


@pytest.mark.parametrize("test_input,expected", [
    ("print fala pessoal", "print('fala pessoal')"),
    ("print sou eu", "print('sou eu')"),
    ("print alguma coisa", "print('alguma coisa')")
])
def test_print_structure(test_input, expected):
    assert expected == pt_translator.print_structure(test_input)


@pytest.mark.parametrize("test_input,expected", [
    ("variável nome recebe string itanu", "nome = str('itanu')"),
    ("variável idade recebe inteiro 20", "idade = int('20')"),
    ("variável altura recebe flutuante 2.30", "altura = float('2.30')")
])
def test_declare_variable(test_input, expected):
    assert expected == pt_translator.declare_variable(test_input)


@pytest.mark.parametrize("test_input,expected", [
    ("defina print idade parâmetro inteiro idade", "def print_idade(idade: int):"),
    ("defina mostrar nome parâmetro string nome", "def mostrar_nome(nome: str):"),
    ("defina retorna um", "def retorna_um():"),
    ("defina print idade e nome parâmetros inteiro idade string nome",
     "def print_idade_e_nome(idade: int, nome: str):")
])
def test_define_function(test_input, expected):
    assert expected == pt_translator.define_function(test_input)


@pytest.mark.parametrize("test_input,expected", [
    ("chame print idade parâmetro inteiro idade", "print_idade(int(idade))"),
    ("chame mostrar nome parâmetro string nome", "mostrar_nome(str(nome))"),
    ("chame retorna um", "retorna_um()"),
    ("chame print idade e nome parâmetros inteiro idade string nome",
     "print_idade_e_nome(int(idade), str(nome))")

])
def test_call_function(test_input, expected):
    assert expected == pt_translator.call_function(test_input)
