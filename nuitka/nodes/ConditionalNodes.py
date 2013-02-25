#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Conditional nodes.

These is the conditional expression '(a if b else c)' and the conditional statement, that
would be 'if a: ... else: ...' and there is no 'elif', because that is expressed via
nesting of conditional statements.
"""

from .NodeBases import ExpressionChildrenHavingBase, StatementChildrenHavingBase


class ExpressionConditional( ExpressionChildrenHavingBase ):
    kind = "EXPRESSION_CONDITIONAL"

    named_children = ( "condition", "expression_yes", "expression_no" )

    def __init__( self, condition, yes_expression, no_expression, source_ref ):
        ExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"      : condition,
                "expression_yes" : yes_expression,
                "expression_no"  : no_expression
            },
            source_ref = source_ref
        )

    def getBranches( self ):
        return ( self.getExpressionYes(), self.getExpressionNo() )

    getExpressionYes = ExpressionChildrenHavingBase.childGetter( "expression_yes" )
    getExpressionNo = ExpressionChildrenHavingBase.childGetter( "expression_no" )
    getCondition = ExpressionChildrenHavingBase.childGetter( "condition" )

    def computeExpression( self, constraint_collection ):
        condition = self.getCondition()

        # If the condition raises, we let that escape.
        if condition.willRaiseException( BaseException ):
            return condition, "new_raise", "Conditional expression raises in condition"

        # Decide this based on truth value of condition.
        truth_value = condition.getTruthValue( constraint_collection )

        if truth_value is True:
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionYes(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to yes case"
            )
        elif truth_value is False:
            from .NodeMakingHelpers import wrapExpressionWithNodeSideEffects

            return (
                wrapExpressionWithNodeSideEffects(
                    new_node = self.getExpressionNo(),
                    old_node = condition
                ),
                "new_expression",
                "Conditional expression predicted to no case"
            )
        else:
            return self, None, None

    def mayHaveSideEffectsBool( self, constraint_collection ):
        if condition.mayHaveSideEffectsBool( constraint_collection ):
            return True

        if self.getExpressionYes().mayHaveSideEffectsBool( constraint_collection ):
            return True

        if self.getExpressionNo().mayHaveSideEffectsBool( constraint_collection ):
            return True

        return False

    def mayProvideReference( self ):
        return self.getExpressionYes().mayProvideReference() or self.getExpressionNo().mayProvideReference()


class StatementConditional( StatementChildrenHavingBase ):
    kind = "STATEMENT_CONDITIONAL"

    named_children = ( "condition", "yes_branch", "no_branch" )

    def __init__( self, condition, yes_branch, no_branch, source_ref ):
        StatementChildrenHavingBase.__init__(
            self,
            values     = {
                "condition"  : condition,
                "yes_branch" : yes_branch,
                "no_branch"  : no_branch
            },
            source_ref = source_ref
        )

    getCondition = StatementChildrenHavingBase.childGetter( "condition" )
    getBranchYes = StatementChildrenHavingBase.childGetter( "yes_branch" )
    setBranchYes = StatementChildrenHavingBase.childSetter( "yes_branch" )
    getBranchNo = StatementChildrenHavingBase.childGetter( "no_branch" )
    setBranchNo = StatementChildrenHavingBase.childSetter( "no_branch" )

    def isStatementAborting( self ):
        yes_branch = self.getBranchYes()

        if yes_branch is not None:
            if yes_branch.isStatementAborting():
                no_branch = self.getBranchNo()

                if no_branch is not None:
                    return no_branch.isStatementAborting()
                else:
                    return False
            else:
                return False
        else:
            return False
