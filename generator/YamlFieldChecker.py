import typing
import numbers
from enum import Enum, auto

from .CppFieldGenerator import CppFieldGenerator
from .CppTypesGenerator import EnumDef, CppTypesGenerator

class YamlFieldCheckResult(Enum):
    OK                               = auto()  # Everything went well
    DISPOSITION_INVALID              = auto()  # Disposition is not known
            
    TYPE_MISSING                     = auto()  # The type field has not been defined
    TYPE_UNKNOWN                     = auto()  # The type is unknown
            
    NAME_MISSING                     = auto()  # The name field has not been defined
    NAME_REDEFINED                   = auto()  # The same name has been used for more than one variable
     
    CONDITION_VAR_NOT_DEFINED        = auto()  # The condition variable has not been defined
    CONDITION_OP_MISSING             = auto()  # The 'condition_operation' key is missing
    CONDITION_OP_UNKNOWN             = auto()  # The condition operator is not known/supported
    CONDITION_VALUE_MISSING          = auto()  # The 'condition_value' key is missing
    CONDITION_VALUE_NOT_DEFINED      = auto()  # The value of 'condition_value' has not been defined elsewhere 
    CONDITION_WITH_ARRAY_ALIAS       = auto()  # Array alias used as left or right hand side

    ARRAY_SIZED_HEADER_MISSING       = auto()
    ARRAY_SIZED_HEADER_TYPE_MISSING  = auto()
 
    ARRAY_SIZE_MISSING               = auto()
    ARRAY_SIZE_UNKNOWN               = auto()
    ARRAY_SIZE_VAR_NOT_BUILTIN_TYPE  = auto()
 
    VALUE_MISSING                    = auto()
    VALUE_NOT_NUMERIC_NOR_ENUM       = auto() 
    VALUE_AND_TYPE_MISMATCH          = auto()



class YamlFieldChecker():

    @staticmethod
    def check_type( class_name: str, field: dict ):
        if "type" not in field:
            field_name = " "  
            if "name" in field:
                field_name = f" '{field['name']}' "

            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for field{field_name}in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def condition( class_name: str, field: dict, member_vars : typing.Dict[str, typing.Tuple[int, str]], user_types: CppTypesGenerator ) -> typing.Tuple[YamlFieldCheckResult, str]:

        # check mandatory fields exists
        if "name" not in field:
            return YamlFieldCheckResult.NAME_MISSING, f"\n\nError: missing 'name' key for field in struct '{class_name}'!\n\n"

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for const field '{field['name']}'' in struct '{class_name}'!\n\n"

        if "condition_operation" not in field:
            return YamlFieldCheckResult.CONDITION_OP_MISSING, f"\n\nError: Condition operator not defined for condition field '{field['name']}'' in struct '{class_name}'!\n\n"

        if "condition_value" not in field:
            return YamlFieldCheckResult.CONDITION_VALUE_MISSING, f"\n\nError: Condition operator not defined for condition field '{field['name']}' in struct '{class_name}'!\n\n"


        # check operation is supported
        cond_op = field["condition_operation"]
        if cond_op not in ["not equals", "equals"]:
            return YamlFieldCheckResult.CONDITION_OP_UNKNOWN, f"\n\nError: Condition operator '{cond_op}' not valid for const field '{field['name']}' in struct '{class_name}'!\n\n"


        # check if 'condition_value' is either an int literal, an int variable or an enum
        lhs_value      = field["condition"]
        rhs_value      = field["condition_value"]
        lhs_is_member  = lhs_value in member_vars
        _, lhs_type    = member_vars[ lhs_value ] if lhs_is_member else (0,"")
        rhs_is_literal = isinstance(rhs_value, int)
        lhs_is_enum    = lhs_type in user_types.name_to_enum
        rhs_is_enum    = lhs_is_enum and rhs_value in user_types.name_to_enum[lhs_type].values
        
        if not rhs_is_literal and rhs_value not in member_vars and not rhs_is_enum:
            return YamlFieldCheckResult.CONDITION_VALUE_NOT_DEFINED, f"\n\nError: Condition value '{field['condition_value']}' not defined in struct '{class_name}'!\n\n"


        # check if left hand side of conditional is a defined variable
        if not lhs_is_member:
            return YamlFieldCheckResult.CONDITION_VAR_NOT_DEFINED, f"\n\nError: Condition variable '{field['condition']}' not defined in struct '{class_name}'!\n\n"


        # check that left hand side (lhs) is not an array alias
        if lhs_type in user_types.name_to_alias and user_types.name_to_alias[lhs_type].size != 1:
            return YamlFieldCheckResult.CONDITION_WITH_ARRAY_ALIAS, f"\n\nError: Condition variable '{lhs_value}' is an array alias!\n\n"


        # check that right hand side (rhs) is not an array alias
        rhs_is_member  = rhs_value in member_vars
        _, rhs_type    = member_vars[ rhs_value ] if rhs_is_member else (0,"")
        if rhs_type in user_types.name_to_alias and user_types.name_to_alias[rhs_type].size != 1:
            return YamlFieldCheckResult.CONDITION_WITH_ARRAY_ALIAS, f"\n\nError: Condition variable '{lhs_value}' is an array alias!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def reserved( class_name: str, field: dict ) -> typing.Tuple[YamlFieldCheckResult, str]:

        if 'value' not in field:
            return YamlFieldCheckResult.VALUE_MISSING, f"\n\nError: 'value' key missing for 'reserved' field in struct '{class_name}'!\n\n"

        value = field['value']

        if not isinstance(value, int):
            return YamlFieldCheckResult.VALUE_NOT_NUMERIC_NOR_ENUM, f"\n\nError: Value of 'reserved' field '{field['name']}' with value '{value}' which is not numeric in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def inline( class_name: str, field: dict, class_decls: dict ) -> typing.Tuple[YamlFieldCheckResult, str]:

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for inline field in struct '{class_name}'!\n\n"

        inline_type = field["type"]
        if inline_type not in class_decls:
            return YamlFieldCheckResult.TYPE_UNKNOWN, f"\n\nError: Type is unknown for inline field in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def const( class_name: str, field: dict, enums : typing.Dict[str, EnumDef ] ):

        if "name" not in field:
            return YamlFieldCheckResult.NAME_MISSING, f"\n\nError: 'const' missing 'name' key in struct '{class_name}'!\n\n"

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for field {field['name']} in struct '{class_name}'!\n\n"

        if 'value' not in field:
            return YamlFieldCheckResult.VALUE_MISSING, f"\n\nError: 'value' key missing for const field '{field['name']}' in struct '{class_name}'!\n\n"

        # check for value and type mismatch
        const_value = field['value']
        const_type  = field["type"]

        if isinstance(const_value, numbers.Number):
            if const_type not in CppFieldGenerator.builtin_types:
                return YamlFieldCheckResult.VALUE_AND_TYPE_MISMATCH, f"\n\nError: value '{const_value}' and type '{const_type}' mismatch for const '{field['name']}' in struct '{class_name}'!\n\n"
        else:
            if const_type not in enums:
                return YamlFieldCheckResult.TYPE_UNKNOWN, f"\n\nError: Type '{const_type}' with value '{const_value}' is unknown for const field '{field['name']}' in struct '{class_name}'!\n\n"

            if const_value not in enums[const_type].values:
                return YamlFieldCheckResult.VALUE_NOT_NUMERIC_NOR_ENUM, f"\n\nError: Value of '{const_value}' of type '{const_type}' for const field '{field['name']}' is not numeric nor enum in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def array( class_name: str, field: dict, field_idx: int, member_vars: typing.Dict[str, typing.Tuple[int, str]] ):
        if "name" not in field:
            return YamlFieldCheckResult.NAME_MISSING, f"\n\nError: 'const' missing 'name' key in struct '{class_name}'!\n\n"

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for field {field['name']} in struct '{class_name}'!\n\n"

        if "size" not in field:
            return YamlFieldCheckResult.ARRAY_SIZE_MISSING, f"\n\nError: Array '{field['name']}' missing 'size' key in struct '{class_name}'!\n\n"

        size_var = str(field["size"])

        if size_var not in member_vars and not size_var.isdigit():
            return YamlFieldCheckResult.ARRAY_SIZE_UNKNOWN, f"\n\nError: Array '{field['name']}' size variable '{size_var}' not defined in struct '{class_name}'!\n\n"

        if not size_var.isdigit():
            _, size_var_type = member_vars[size_var]
            if size_var_type not in CppFieldGenerator.builtin_types and size_var_type != "varint":
                return YamlFieldCheckResult.ARRAY_SIZE_VAR_NOT_BUILTIN_TYPE, f"\n\nError: Array '{field['name']}' size variable '{size_var}' type '{size_var_type}' not an integer type in struct '{class_name}'!\n\n"

        # TODO: move this test to ConsistencyChecker!!
        #idx, _ = member_vars[size_var]
        #if idx > field_idx:
        #    return DeclGenResult.ARRAY_SIZE_VAR_DEFINED_AFTER, f"\n\nError: Array '{field['name']}' size variable '{size_var}' defined after array in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""

    @staticmethod
    def array_sized( class_name: str, field: dict ) -> typing.Tuple[YamlFieldCheckResult, str]:
        if "name" not in field:
            return YamlFieldCheckResult.NAME_MISSING, f"\n\nError: array_sized missing 'name' key in struct '{class_name}'!\n\n"

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for field {field['name']} in struct '{class_name}'!\n\n"

        if "header_type_field" not in field:
            return YamlFieldCheckResult.ARRAY_SIZED_HEADER_TYPE_MISSING, f"\n\nError: array_sized '{field['name']}' missing 'header_type_field' key in struct '{class_name}'!\n\n"

        if "size" not in field:
            return YamlFieldCheckResult.ARRAY_SIZE_MISSING, f"\n\nError: array_sized '{field['name']}' missing 'size' key in struct '{class_name}'!\n\n"

        return YamlFieldCheckResult.OK, ""


    @staticmethod
    def array_fill( class_name: str, field: dict, class_decls: dict ) -> typing.Tuple[YamlFieldCheckResult, str]:
        if "name" not in field:
            return YamlFieldCheckResult.NAME_MISSING, f"\n\nError: array_fill missing 'name' field in struct '{class_name}'!\n\n"

        if 'type' not in field:
            return YamlFieldCheckResult.TYPE_MISSING, f"\n\nError: Missing 'type' key for array_fill field '{field['name']}' in struct '{class_name}'!\n\n"

        array_type = field["type"]
        if array_type not in class_decls and array_type not in CppFieldGenerator.builtin_types:
            return YamlFieldCheckResult.TYPE_UNKNOWN, f"\n\nError: Type '{array_type}' is unknown for array_fill field '{field['name']}' in struct '{class_name}'!\n\n"
        
        return YamlFieldCheckResult.OK, ""
